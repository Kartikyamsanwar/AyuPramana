"""Ingestion pipeline: manifest entry → file hash → text → chunks → SQLite + Chroma.

Versioning: every file is identified by its SHA-256 hash. If the hash changes, a new
DocumentVersion is created and the previous version's chunks are marked inactive
(kept for audit, never retrieved). Re-running on an unchanged file does nothing,
except re-embedding when the embedding model has changed.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select, update

from app.config import Settings
from app.db.models import Chunk, Document, DocumentVersion
from app.db.session import SessionFactory
from app.ingest.chunker import ChunkDraft, chunk_document
from app.ingest.loaders import UnsupportedFileError, load_document
from app.ingest.manifest import ManifestEntry, load_manifest
from app.retrieval.embeddings import Embedder
from app.retrieval.vector_store import VectorStore

log = logging.getLogger(__name__)


@dataclass
class IngestResult:
    doc_id: str
    title: str
    jurisdiction: str
    status: str  # ingested | unchanged | reembedded | missing_file | no_text | error | unknown_id
    chunks: int = 0
    version: str = ""
    message: str = ""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _vector_metadata(entry: ManifestEntry, version: DocumentVersion, chunk: Chunk) -> dict:
    """Filter fields stored next to each vector. Text and citation details are read from SQLite."""
    return {
        "doc_id": entry.id,
        "jurisdiction": entry.jurisdiction,
        "domain": entry.domain,
        "doc_type": entry.doc_type,
        "kind": chunk.kind,
        "version": version.short_hash,
        "active": True,
    }


class Ingestor:
    def __init__(
        self,
        settings: Settings,
        session_factory: SessionFactory,
        vector_store: VectorStore,
        embedder: Embedder,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.vector_store = vector_store
        self.embedder = embedder

    def ingest(self, doc_ids: list[str] | None = None, force: bool = False) -> list[IngestResult]:
        """Ingest all manifest entries, or only `doc_ids`. `force` rebuilds even unchanged files."""
        entries = load_manifest(self.settings.manifest_path)
        by_id = {e.id: e for e in entries}
        results: list[IngestResult] = []
        if doc_ids:
            for unknown in [d for d in doc_ids if d not in by_id]:
                results.append(IngestResult(unknown, "", "", "unknown_id", message="not in manifest.yaml"))
            entries = [by_id[d] for d in doc_ids if d in by_id]
        for entry in entries:
            try:
                results.append(self._ingest_entry(entry, force))
            except UnsupportedFileError as exc:
                results.append(IngestResult(entry.id, entry.title, entry.jurisdiction, "error", message=str(exc)))
            except Exception as exc:  # keep going; report the failure in the summary
                log.exception("Ingestion failed for %s", entry.id)
                results.append(IngestResult(entry.id, entry.title, entry.jurisdiction, "error", message=repr(exc)))
        return results

    # ------------------------------------------------------------------
    def _ingest_entry(self, entry: ManifestEntry, force: bool) -> IngestResult:
        path = self.settings.raw_dir / entry.file
        result = IngestResult(entry.id, entry.title, entry.jurisdiction, "missing_file")
        if not path.exists():
            result.message = f"file not found: data/raw/{entry.file}"
            return result

        file_hash = file_sha256(path)
        with self.session_factory() as session:
            document = session.get(Document, entry.id) or Document(id=entry.id)
            document.title = entry.title
            document.jurisdiction = entry.jurisdiction
            document.domain = entry.domain
            document.doc_type = entry.doc_type
            document.source_url = entry.source_url
            document.file = entry.file
            session.add(document)

            active = session.scalars(
                select(DocumentVersion).where(
                    DocumentVersion.doc_id == entry.id, DocumentVersion.is_active.is_(True)
                )
            ).first()

            if active is not None and active.file_hash == file_hash and not force:
                active.version_date = entry.version_date
                self._sync_chunk_fields(session, active, entry)
                reembedded = self._ensure_vectors(session, entry, active)
                session.commit()
                result.status = "reembedded" if reembedded else "unchanged"
                result.chunks, result.version = active.chunk_count, active.short_hash
                return result

            pages = load_document(path)
            drafts = chunk_document(
                pages,
                doc_type=entry.doc_type,
                section_label=entry.section_label,
                target_tokens=self.settings.chunk_target_tokens,
                max_tokens=self.settings.chunk_max_tokens,
                overlap_tokens=self.settings.chunk_overlap_tokens,
            )
            if not drafts:
                session.rollback()
                result.status = "no_text"
                result.message = "no extractable text (scanned PDF? run OCR first)"
                return result

            # A forced rebuild of the same file replaces that version's rows
            for stale in session.scalars(
                select(DocumentVersion).where(
                    DocumentVersion.doc_id == entry.id, DocumentVersion.file_hash == file_hash
                )
            ).all():
                self.vector_store.delete([c.id for c in stale.chunks])
                session.delete(stale)
            session.flush()

            # Retire older versions
            old_ids = list(
                session.scalars(select(Chunk.id).where(Chunk.doc_id == entry.id, Chunk.is_active.is_(True)))
            )
            session.execute(update(Chunk).where(Chunk.doc_id == entry.id).values(is_active=False))
            session.execute(
                update(DocumentVersion).where(DocumentVersion.doc_id == entry.id).values(is_active=False)
            )

            version = DocumentVersion(
                doc_id=entry.id,
                file_hash=file_hash,
                version_date=entry.version_date,
                chunk_count=len(drafts),
                is_active=True,
            )
            session.add(version)
            session.flush()
            chunks = [self._make_chunk(entry, version, draft) for draft in drafts]
            session.add_all(chunks)
            session.flush()

            embeddings = self.embedder.embed_documents([c.text for c in chunks])
            self.vector_store.upsert(
                [c.id for c in chunks], embeddings, [_vector_metadata(entry, version, c) for c in chunks]
            )
            self.vector_store.set_active(old_ids, False)
            session.commit()

            result.status = "ingested"
            result.chunks, result.version = len(chunks), version.short_hash
            return result

    @staticmethod
    def _make_chunk(entry: ManifestEntry, version: DocumentVersion, draft: ChunkDraft) -> Chunk:
        return Chunk(
            id=f"{entry.id}:{version.short_hash}:{draft.ordinal:04d}",
            version_id=version.id,
            doc_id=entry.id,
            ordinal=draft.ordinal,
            section_ref=draft.section_ref,
            heading=draft.heading,
            kind=draft.kind,
            page=draft.page,
            text=draft.text,
            token_estimate=draft.token_estimate,
            jurisdiction=entry.jurisdiction,
            domain=entry.domain,
            doc_type=entry.doc_type,
            is_active=True,
        )

    @staticmethod
    def _sync_chunk_fields(session, version: DocumentVersion, entry: ManifestEntry) -> None:
        """Manifest edits to jurisdiction/domain/doc_type apply without re-chunking."""
        session.execute(
            update(Chunk)
            .where(Chunk.version_id == version.id)
            .values(jurisdiction=entry.jurisdiction, domain=entry.domain, doc_type=entry.doc_type)
        )

    def _ensure_vectors(self, session, entry: ManifestEntry, version: DocumentVersion) -> bool:
        """Embed (or refresh metadata of) an unchanged version, e.g. after switching embedding model."""
        chunks = session.scalars(select(Chunk).where(Chunk.version_id == version.id).order_by(Chunk.ordinal)).all()
        ids = [c.id for c in chunks]
        present = self.vector_store.existing_ids(ids)
        missing = [c for c in chunks if c.id not in present]
        if missing:
            embeddings = self.embedder.embed_documents([c.text for c in missing])
            self.vector_store.upsert(
                [c.id for c in missing], embeddings, [_vector_metadata(entry, version, c) for c in missing]
            )
        # Keep filter metadata in step with the manifest
        existing = [c for c in chunks if c.id in present]
        if existing:
            self.vector_store.update_metadata(
                [c.id for c in existing], [_vector_metadata(entry, version, c) for c in existing]
            )
        return bool(missing)

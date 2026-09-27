"""Read helpers over the corpus tables, shared by retrieval, the sources page and health checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from sqlalchemy import func, select

from app.db.models import Chunk, Document, DocumentVersion
from app.db.session import SessionFactory


@dataclass(frozen=True)
class ChunkView:
    """An active chunk joined with its document and version — everything a citation needs."""

    chunk_id: str
    doc_id: str
    title: str
    jurisdiction: str
    domain: str
    doc_type: str
    version_date: str
    version: str
    section_ref: str
    heading: str
    kind: str
    page: int | None
    source_url: str
    file: str
    text: str


def _views(rows: Iterable[tuple[Chunk, Document, DocumentVersion]]) -> list[ChunkView]:
    return [
        ChunkView(
            chunk_id=chunk.id,
            doc_id=doc.id,
            title=doc.title,
            jurisdiction=doc.jurisdiction,
            domain=doc.domain,
            doc_type=doc.doc_type,
            version_date=version.version_date,
            version=version.short_hash,
            section_ref=chunk.section_ref,
            heading=chunk.heading,
            kind=chunk.kind,
            page=chunk.page,
            source_url=doc.source_url,
            file=doc.file,
            text=chunk.text,
        )
        for chunk, doc, version in rows
    ]


class CorpusRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _active_query(self):
        return (
            select(Chunk, Document, DocumentVersion)
            .join(DocumentVersion, Chunk.version_id == DocumentVersion.id)
            .join(Document, Chunk.doc_id == Document.id)
            .where(Chunk.is_active.is_(True), DocumentVersion.is_active.is_(True))
        )

    def get_active_chunks(self, chunk_ids: Sequence[str]) -> dict[str, ChunkView]:
        """Look up chunks by id; ids that are unknown or inactive are silently dropped."""
        if not chunk_ids:
            return {}
        with self._session_factory() as session:
            rows = session.execute(self._active_query().where(Chunk.id.in_(list(chunk_ids)))).all()
        return {view.chunk_id: view for view in _views(rows)}

    def active_chunks_for(self, jurisdiction: str) -> list[ChunkView]:
        """All retrievable chunks of one jurisdiction (tables of contents excluded) — used to build BM25."""
        with self._session_factory() as session:
            rows = session.execute(
                self._active_query()
                .where(Chunk.jurisdiction == jurisdiction, Chunk.kind != "toc")
                .order_by(Chunk.doc_id, Chunk.ordinal)
            ).all()
        return _views(rows)

    def active_chunk_count(self, jurisdiction: str) -> int:
        with self._session_factory() as session:
            count = session.scalar(
                select(func.count())
                .select_from(Chunk)
                .where(Chunk.jurisdiction == jurisdiction, Chunk.is_active.is_(True))
            )
        return int(count or 0)

    def revision(self) -> tuple[int, int]:
        """Changes whenever ingestion adds or retires a version; used to invalidate in-memory indexes."""
        with self._session_factory() as session:
            max_version = session.scalar(select(func.max(DocumentVersion.id))) or 0
            active = session.scalar(
                select(func.count()).select_from(DocumentVersion).where(DocumentVersion.is_active.is_(True))
            )
        return int(max_version), int(active or 0)

    def corpus_counts(self) -> tuple[int, int]:
        """(documents with an active version, active chunks)."""
        with self._session_factory() as session:
            docs = session.scalar(
                select(func.count(func.distinct(DocumentVersion.doc_id))).where(DocumentVersion.is_active.is_(True))
            )
            chunks = session.scalar(select(func.count()).select_from(Chunk).where(Chunk.is_active.is_(True)))
        return int(docs or 0), int(chunks or 0)

    def documents_with_versions(self) -> list[tuple[Document, list[DocumentVersion]]]:
        with self._session_factory() as session:
            docs = session.scalars(select(Document).order_by(Document.jurisdiction, Document.id)).all()
            return [
                (doc, sorted(doc.versions, key=lambda v: v.ingested_at, reverse=True))
                for doc in docs
            ]

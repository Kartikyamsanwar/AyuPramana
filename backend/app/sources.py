"""Builds the corpus listing for the Sources page: manifest entries merged with what is ingested."""

from __future__ import annotations

from app.config import Settings
from app.db.models import DocumentVersion
from app.db.repository import CorpusRepository
from app.ingest.manifest import ManifestError, load_manifest
from app.schemas import SourceDocument, SourcesResponse, SourceVersion


def _version(v: DocumentVersion) -> SourceVersion:
    return SourceVersion(
        version=v.short_hash,
        version_date=v.version_date,
        ingested_at=v.ingested_at.isoformat(timespec="seconds"),
        chunk_count=v.chunk_count,
        active=v.is_active,
    )


def list_sources(settings: Settings, repository: CorpusRepository) -> SourcesResponse:
    manifest_error = None
    try:
        entries = load_manifest(settings.manifest_path)
    except ManifestError as exc:
        entries, manifest_error = [], str(exc)

    ingested = {doc.id: (doc, versions) for doc, versions in repository.documents_with_versions()}
    documents: list[SourceDocument] = []

    for entry in entries:
        doc_versions = ingested.pop(entry.id, (None, []))[1]
        versions = [_version(v) for v in doc_versions]
        active = next((v for v in versions if v.active), None)
        if active:
            status = "ingested"
        elif (settings.raw_dir / entry.file).exists():
            status = "pending"
        else:
            status = "missing_file"
        documents.append(
            SourceDocument(
                id=entry.id,
                title=entry.title,
                jurisdiction=entry.jurisdiction,
                domain=entry.domain,
                doc_type=entry.doc_type,
                source_url=entry.source_url,
                file=entry.file,
                status=status,
                active_version=active,
                versions=versions,
            )
        )

    # Ingested earlier but no longer in the manifest (still searchable until re-ingested/cleaned)
    for doc, doc_versions in ingested.values():
        versions = [_version(v) for v in doc_versions]
        documents.append(
            SourceDocument(
                id=doc.id,
                title=doc.title,
                jurisdiction=doc.jurisdiction,
                domain=doc.domain,
                doc_type=doc.doc_type,
                source_url=doc.source_url,
                file=doc.file,
                status="removed_from_manifest",
                active_version=next((v for v in versions if v.active), None),
                versions=versions,
            )
        )
    return SourcesResponse(documents=documents, manifest_error=manifest_error)

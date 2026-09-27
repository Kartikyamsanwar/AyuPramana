"""SQLAlchemy models.

SQLite is the source of truth for documents, versions and chunk text. Chroma only
holds the vectors (plus filter metadata), so a search result is always re-read
from here and inactive (superseded) chunks can never leak into an answer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Document(Base):
    """One manifest entry (a statute, rules, treaty…)."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    jurisdiction: Mapped[str] = mapped_column(String(20), index=True)
    domain: Mapped[str] = mapped_column(String(30))
    doc_type: Mapped[str] = mapped_column(String(30))
    source_url: Mapped[str] = mapped_column(String(1000), default="")
    file: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    versions: Mapped[list[DocumentVersion]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """A specific file (identified by its SHA-256 hash) ingested for a document."""

    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    file_hash: Mapped[str] = mapped_column(String(64))
    version_date: Mapped[str] = mapped_column(String(10))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    document: Mapped[Document] = relationship(back_populates="versions")
    chunks: Mapped[list[Chunk]] = relationship(back_populates="version", cascade="all, delete-orphan")

    @property
    def short_hash(self) -> str:
        return self.file_hash[:10]


class Chunk(Base):
    """A section-aligned piece of a document version. Filter fields are copied from the document for fast search."""

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(150), primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("document_versions.id"), index=True)
    doc_id: Mapped[str] = mapped_column(String(100), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    section_ref: Mapped[str] = mapped_column(String(200))
    heading: Mapped[str] = mapped_column(String(300), default="")
    kind: Mapped[str] = mapped_column(String(20), default="provision")  # provision | preamble | toc
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    jurisdiction: Mapped[str] = mapped_column(String(20), index=True)
    domain: Mapped[str] = mapped_column(String(30), index=True)
    doc_type: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    version: Mapped[DocumentVersion] = relationship(back_populates="chunks")


class QueryLog(Base):
    """Audit record for one chat turn. Only PII-scrubbed text and an anonymous session id are stored."""

    __tablename__ = "query_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    language: Mapped[str] = mapped_column(String(5))
    jurisdiction: Mapped[str] = mapped_column(String(20))
    query_text: Mapped[str] = mapped_column(Text)
    intents: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    blocks_summary: Mapped[str] = mapped_column(Text, default="{}")  # JSON: per-jurisdiction confidence/abstained
    min_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    abstained: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    llm_provider: Mapped[str] = mapped_column(String(20), default="")
    source: Mapped[str] = mapped_column(String(10), default="chat")  # chat | eval


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[int | None] = mapped_column(ForeignKey("query_log.id"), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64))
    jurisdiction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rating: Mapped[str] = mapped_column(String(4))  # up | down
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Escalation(Base):
    """A request to talk to a human IP facilitator (logged only; nothing is sent)."""

    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[int | None] = mapped_column(ForeignKey("query_log.id"), nullable=True)
    session_id: Mapped[str] = mapped_column(String(64))
    jurisdiction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

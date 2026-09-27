"""Retriever: finds the chunks most relevant to a question, strictly within one jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from app.db.repository import ChunkView, CorpusRepository
from app.retrieval.embeddings import Embedder
from app.retrieval.vector_store import VectorStore, build_where

JURISDICTIONS = ("india", "international")


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk plus the scores that explain why it was retrieved."""

    chunk: ChunkView
    vector_score: float | None = None  # cosine similarity
    bm25_score: float | None = None
    fused_score: float = 0.0
    rerank_score: float | None = None  # 0-1 when the reranker is enabled
    relevance: float = 0.0  # calibrated 0-1 relevance used for confidence
    in_vector: bool = False
    in_bm25: bool = False

    def with_(self, **changes) -> RetrievedChunk:
        return replace(self, **changes)


class Retriever:
    def __init__(
        self,
        repository: CorpusRepository,
        vector_store: VectorStore,
        embedder: Embedder,
        top_k: int = 6,
        candidates: int = 30,
    ) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = top_k
        self.candidates = candidates

    def search(
        self,
        query: str,
        jurisdiction: str,
        domains: Sequence[str] | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Vector search filtered by jurisdiction (required — never mixed) and optionally by domain."""
        if jurisdiction not in JURISDICTIONS:
            raise ValueError(f"jurisdiction must be one of {JURISDICTIONS}, got {jurisdiction!r}")
        k = top_k or self.top_k
        where = build_where(
            jurisdiction=jurisdiction,
            active=True,
            domain=list(domains) if domains else None,
            kind=["provision", "preamble"],
        )
        hits = self.vector_store.query(self.embedder.embed_query(query), self.candidates, where)
        views = self.repository.get_active_chunks([chunk_id for chunk_id, _ in hits])
        results = [
            RetrievedChunk(chunk=views[cid], vector_score=score, fused_score=score, relevance=score, in_vector=True)
            for cid, score in hits
            if cid in views and views[cid].jurisdiction == jurisdiction
        ]
        return results[:k]

"""Hybrid retriever: vector search + BM25, merged by reciprocal rank fusion, optionally reranked.

Every search is restricted to ONE jurisdiction (India or International), so the two
regimes can never be mixed in the evidence for an answer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from app.db.repository import ChunkView, CorpusRepository
from app.retrieval.bm25 import BM25Search
from app.retrieval.embeddings import Embedder
from app.retrieval.reranker import Reranker
from app.retrieval.vector_store import VectorStore, build_where

JURISDICTIONS = ("india", "international")
RRF_K = 60  # standard reciprocal-rank-fusion constant


def default_similarity_range(model_name: str) -> tuple[float, float]:
    """Typical cosine similarity of an unrelated vs. a clearly relevant passage, per embedding model.

    Used to map raw similarity to a 0-1 relevance. These are starting points: tune
    SIMILARITY_FLOOR / SIMILARITY_CEILING in .env after running scripts/eval.py.
    """
    name = model_name.lower()
    if name.startswith("gemini/"):
        return 0.45, 0.80  # provisional; calibrate with scripts/eval.py
    if "e5" in name:
        return 0.75, 0.88
    if "bge-m3" in name:
        return 0.40, 0.72
    return 0.0, 1.0


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk plus the scores that explain why it was retrieved."""

    chunk: ChunkView
    vector_score: float | None = None  # cosine similarity
    bm25_score: float | None = None
    fused_score: float = 0.0  # reciprocal rank fusion score
    rerank_score: float | None = None  # 0-1 when the reranker is enabled
    relevance: float = 0.0  # calibrated 0-1 relevance used for confidence
    in_vector: bool = False  # found by vector search
    in_bm25: bool = False  # found by keyword search

    def with_(self, **changes) -> RetrievedChunk:
        return replace(self, **changes)


class Retriever:
    def __init__(
        self,
        repository: CorpusRepository,
        vector_store: VectorStore,
        embedder: Embedder,
        bm25: BM25Search | None = None,
        reranker: Reranker | None = None,
        top_k: int = 6,
        candidates: int = 30,
        similarity_range: tuple[float, float] | None = None,
    ) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.embedder = embedder
        self.bm25 = bm25 or BM25Search(repository)
        self.reranker = reranker
        self.top_k = top_k
        self.candidates = candidates
        self.similarity_range = similarity_range or default_similarity_range(embedder.model_name)

    def _calibrate(self, similarity: float | None) -> float:
        if similarity is None:
            return 0.0
        floor, ceiling = self.similarity_range
        return max(0.0, min(1.0, (similarity - floor) / max(ceiling - floor, 1e-6)))

    def search(
        self,
        query: str,
        jurisdiction: str,
        domains: Sequence[str] | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Top chunks for `query` within one jurisdiction (and optional domains), best first."""
        if jurisdiction not in JURISDICTIONS:
            raise ValueError(f"jurisdiction must be one of {JURISDICTIONS}, got {jurisdiction!r}")
        k = top_k or self.top_k
        domains = list(domains) if domains else None

        # 1. Vector search (Chroma metadata filter), then re-read text from SQLite (active chunks only)
        query_vector = self.embedder.embed_query(query)
        where = build_where(jurisdiction=jurisdiction, active=True, domain=domains, kind=["provision", "preamble"])
        vector_hits = self.vector_store.query(query_vector, self.candidates, where)
        views = self.repository.get_active_chunks([cid for cid, _ in vector_hits])
        vector_ranked = [(views[cid], sim) for cid, sim in vector_hits if cid in views]

        # 2. Keyword search
        bm25_ranked = self.bm25.search(query, jurisdiction, domains, self.candidates)

        # 3. Reciprocal rank fusion
        fused: dict[str, RetrievedChunk] = {}
        for rank, (view, similarity) in enumerate(vector_ranked):
            fused[view.chunk_id] = RetrievedChunk(
                chunk=view, vector_score=similarity, fused_score=1 / (RRF_K + rank + 1), in_vector=True
            )
        for rank, (view, score) in enumerate(bm25_ranked):
            item = fused.get(view.chunk_id) or RetrievedChunk(chunk=view)
            fused[view.chunk_id] = item.with_(
                bm25_score=score, fused_score=item.fused_score + 1 / (RRF_K + rank + 1), in_bm25=True
            )
        ranked = sorted(fused.values(), key=lambda r: r.fused_score, reverse=True)
        # Defensive: never return another jurisdiction's chunk, whatever the stores say
        ranked = [r for r in ranked if r.chunk.jurisdiction == jurisdiction]
        pool = ranked[: max(k * 2, 12)]

        # Keyword-only hits have no similarity yet — compute it so relevance is comparable
        missing = [r.chunk.chunk_id for r in pool if r.vector_score is None]
        if missing:
            sims = self.vector_store.similarities(query_vector, missing)
            pool = [r.with_(vector_score=sims.get(r.chunk.chunk_id)) if r.vector_score is None else r for r in pool]

        # 4. Relevance: reranker probability if enabled, else calibrated cosine similarity
        if self.reranker is not None and pool:
            scores = self.reranker.score(query, [r.chunk.text for r in pool])
            pool = [r.with_(rerank_score=s, relevance=s) for r, s in zip(pool, scores)]
            pool.sort(key=lambda r: r.rerank_score or 0.0, reverse=True)
        else:
            pool = [r.with_(relevance=self._calibrate(r.vector_score)) for r in pool]
        return pool[:k]

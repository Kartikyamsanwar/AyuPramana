"""BM25 keyword index, one per jurisdiction, rebuilt automatically after ingestion.

Keyword search catches exact legal terms ("benefit sharing", "Schedule E(1)") that
embeddings can blur; vector search catches paraphrases. Hybrid search uses both.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Sequence

from rank_bm25 import BM25Okapi

from app.db.repository import ChunkView, CorpusRepository

_STOPWORDS = frozenset(
    "a an and are as at be by can do does for from has have how i if in into is it its may my of on or "
    "our shall should that the their them there these this to under was we what when where which who "
    "will with without would you your".split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens (Unicode-aware, so Devanagari works too), minus common stopwords."""
    return [t for t in re.findall(r"\w+", text.lower()) if len(t) > 1 and t not in _STOPWORDS]


@dataclass
class _Index:
    revision: tuple[int, int]
    chunks: list[ChunkView]
    bm25: BM25Okapi | None


class BM25Search:
    def __init__(self, repository: CorpusRepository) -> None:
        self.repository = repository
        self._indexes: dict[str, _Index] = {}
        self._lock = threading.Lock()

    def _index_for(self, jurisdiction: str) -> _Index:
        revision = self.repository.revision()
        with self._lock:
            index = self._indexes.get(jurisdiction)
            if index is None or index.revision != revision:
                chunks = self.repository.active_chunks_for(jurisdiction)
                corpus = [tokenize(f"{c.section_ref} {c.heading} {c.text}") for c in chunks]
                bm25 = BM25Okapi(corpus) if corpus else None
                index = _Index(revision, chunks, bm25)
                self._indexes[jurisdiction] = index
        return index

    def search(
        self, query: str, jurisdiction: str, domains: Sequence[str] | None, limit: int
    ) -> list[tuple[ChunkView, float]]:
        """Top `limit` chunks with a positive BM25 score, within one jurisdiction (and domains)."""
        index = self._index_for(jurisdiction)
        tokens = tokenize(query)
        if index.bm25 is None or not tokens:
            return []
        scores = index.bm25.get_scores(tokens)
        allowed = set(domains) if domains else None
        ranked = sorted(
            (
                (chunk, float(score))
                for chunk, score in zip(index.chunks, scores)
                if score > 0 and (allowed is None or chunk.domain in allowed)
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return ranked[:limit]

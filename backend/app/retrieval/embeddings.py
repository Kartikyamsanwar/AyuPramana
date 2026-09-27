"""Multilingual sentence embeddings (sentence-transformers), loaded lazily on first use."""

from __future__ import annotations

import threading
from typing import Protocol, Sequence


class Embedder(Protocol):
    model_name: str

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    """Wraps a sentence-transformers model.

    E5 models expect "query: " / "passage: " prefixes; BGE-M3 needs none. Vectors are
    L2-normalised, so cosine similarity equals the dot product.
    """

    def __init__(self, model_name: str, device: str = "cpu", batch_size: int = 16) -> None:
        self.model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model = None
        self._lock = threading.Lock()
        is_e5 = "e5" in model_name.lower()
        self._query_prefix = "query: " if is_e5 else ""
        self._passage_prefix = "passage: " if is_e5 else ""

    def _load(self):
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device=self._device)
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(
            [self._passage_prefix + t for t in texts],
            batch_size=self._batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 64,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        model = self._load()
        return model.encode(self._query_prefix + text, normalize_embeddings=True).tolist()

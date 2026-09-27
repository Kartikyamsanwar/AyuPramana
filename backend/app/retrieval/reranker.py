"""Optional cross-encoder reranker (RERANKER_ENABLED=true).

A cross-encoder reads the question and a chunk together and outputs a relevance
probability (0-1). It is slower than embeddings, so it only re-scores the top candidates.
"""

from __future__ import annotations

import threading
from typing import Protocol, Sequence


class Reranker(Protocol):
    def score(self, query: str, texts: Sequence[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(self, model_name: str, device: str = "cpu", max_length: int = 512) -> None:
        self.model_name = model_name
        self._device = device
        self._max_length = max_length
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self.model_name, device=self._device, max_length=self._max_length)
        return self._model

    def score(self, query: str, texts: Sequence[str]) -> list[float]:
        if not texts:
            return []
        import torch

        model = self._load()
        scores = model.predict([(query, t) for t in texts], activation_fn=torch.nn.Sigmoid(), batch_size=8)
        return [float(s) for s in scores]

"""Embeddings from Google's Gemini API (EMBEDDING_PROVIDER=gemini).

Used for low-memory hosting: no PyTorch or local model is loaded, so the backend fits
in a 512 MB instance. Vectors are L2-normalised so cosine similarity equals the dot
product, exactly like the local embedder.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Sequence

import httpx

log = logging.getLogger(__name__)

API = "https://generativelanguage.googleapis.com/v1beta/models"
RETRYABLE = {429, 500, 502, 503, 504}


class EmbeddingError(RuntimeError):
    pass


def _normalise(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


class GeminiEmbedder:
    """`gemini-embedding-001` takes a task type; newer models take the task inside the text."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-2",
        dimensions: int = 768,
        batch_size: int = 50,
        timeout: float = 60.0,
        max_retries: int = 4,
    ) -> None:
        if not api_key:
            raise EmbeddingError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        self._key = api_key
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._timeout = timeout
        self._max_retries = max_retries
        self._task_types = "embedding-001" in model
        # Also names the vector collection, so switching model or size never mixes vectors
        self.model_name = f"gemini/{model}-{dimensions}"

    def _request(self, kind: str, text: str) -> dict:
        request: dict = {
            "model": f"models/{self._model}",
            "outputDimensionality": self._dimensions,
        }
        if self._task_types:
            request["taskType"] = "RETRIEVAL_QUERY" if kind == "query" else "RETRIEVAL_DOCUMENT"
        else:
            text = f"task: search result | query: {text}" if kind == "query" else f"title: none | text: {text}"
        request["content"] = {"parts": [{"text": text}]}
        return request

    def _batch(self, kind: str, texts: Sequence[str]) -> list[list[float]]:
        url = f"{API}/{self._model}:batchEmbedContents"
        body = {"requests": [self._request(kind, t) for t in texts]}
        last_error = ""
        for attempt in range(self._max_retries + 1):
            try:
                response = httpx.post(url, json=body, headers={"x-goog-api-key": self._key}, timeout=self._timeout)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code == 200:
                    embeddings = response.json().get("embeddings", [])
                    if len(embeddings) != len(texts):
                        raise EmbeddingError("Gemini returned the wrong number of embeddings")
                    return [_normalise(e["values"]) for e in embeddings]
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
                if response.status_code not in RETRYABLE:
                    break
            if attempt < self._max_retries:
                time.sleep(min(2 ** (attempt + 1), 30))
        raise EmbeddingError(f"Gemini embeddings failed: {last_error}")

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            vectors.extend(self._batch("document", texts[start : start + self._batch_size]))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._batch("query", [text])[0]

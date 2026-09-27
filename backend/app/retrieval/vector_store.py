"""ChromaDB wrapper: stores one vector per chunk with filter metadata (jurisdiction, domain, active…)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings


def collection_name_for(model_name: str) -> str:
    """One collection per embedding model, because vectors from different models are not comparable."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", model_name).strip("-").lower()
    return f"chunks-{slug}"[:60].rstrip("-")


def build_where(**conditions: Any) -> dict[str, Any] | None:
    """Build a Chroma `where` filter. List values become `$in`; None values are skipped."""
    clauses = []
    for key, value in conditions.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            clauses.append({key: {"$in": list(value)}})
        else:
            clauses.append({key: value})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


class VectorStore:
    def __init__(self, persist_dir: Path, model_name: str) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir), settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            collection_name_for(model_name), metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, ids: Sequence[str], embeddings: Sequence[Sequence[float]], metadatas: Sequence[dict]) -> None:
        if ids:
            self._collection.upsert(ids=list(ids), embeddings=[list(e) for e in embeddings], metadatas=list(metadatas))

    def set_active(self, ids: Sequence[str], active: bool) -> None:
        """Flip the `active` flag on existing vectors (used when a newer document version replaces them)."""
        if not ids:
            return
        existing = self._collection.get(ids=list(ids), include=["metadatas"])
        if not existing["ids"]:
            return
        metadatas = [{**(meta or {}), "active": active} for meta in existing["metadatas"]]
        self._collection.update(ids=existing["ids"], metadatas=metadatas)

    def update_metadata(self, ids: Sequence[str], metadatas: Sequence[dict]) -> None:
        if ids:
            self._collection.update(ids=list(ids), metadatas=list(metadatas))

    def delete(self, ids: Sequence[str]) -> None:
        if ids:
            self._collection.delete(ids=list(ids))

    def existing_ids(self, ids: Sequence[str]) -> set[str]:
        if not ids:
            return set()
        return set(self._collection.get(ids=list(ids), include=[])["ids"])

    def similarities(self, embedding: Sequence[float], ids: Sequence[str]) -> dict[str, float]:
        """Cosine similarity between a query vector and specific chunks (vectors are normalised)."""
        if not ids:
            return {}
        stored = self._collection.get(ids=list(ids), include=["embeddings"])
        return {
            chunk_id: float(sum(a * b for a, b in zip(embedding, vector)))
            for chunk_id, vector in zip(stored["ids"], stored["embeddings"])
        }

    def count(self) -> int:
        return self._collection.count()

    def query(self, embedding: Sequence[float], n_results: int, where: dict | None) -> list[tuple[str, float]]:
        """Return (chunk_id, cosine similarity) pairs, best first."""
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[list(embedding)],
            n_results=n_results,
            where=where,
            include=["distances"],
        )
        ids = result["ids"][0]
        distances = result["distances"][0]
        return [(chunk_id, 1.0 - float(distance)) for chunk_id, distance in zip(ids, distances)]

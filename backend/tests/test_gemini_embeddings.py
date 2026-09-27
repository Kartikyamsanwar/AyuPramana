"""Gemini embeddings client: request shape, normalisation, batching (no network)."""

import math

import httpx

from app.retrieval.gemini_embeddings import GeminiEmbedder


def fake_post(calls):
    def post(url, json=None, headers=None, timeout=None):
        calls.append((url, json, headers))
        embeddings = [{"values": [3.0, 4.0]} for _ in json["requests"]]
        return httpx.Response(200, json={"embeddings": embeddings}, request=httpx.Request("POST", url))

    return post


def test_documents_are_batched_normalised_and_prefixed(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(httpx, "post", fake_post(calls))
    embedder = GeminiEmbedder("test-key", "gemini-embedding-2", dimensions=2, batch_size=2)
    vectors = embedder.embed_documents(["a", "b", "c"])
    assert len(vectors) == 3 and len(calls) == 2  # batches of 2
    assert math.isclose(vectors[0][0], 0.6) and math.isclose(vectors[0][1], 0.8)
    url, body, headers = calls[0]
    assert url.endswith("/gemini-embedding-2:batchEmbedContents")
    assert headers == {"x-goog-api-key": "test-key"}
    assert body["requests"][0]["content"]["parts"][0]["text"] == "title: none | text: a"
    assert body["requests"][0]["outputDimensionality"] == 2
    assert embedder.model_name == "gemini/gemini-embedding-2-2"


def test_legacy_model_uses_task_types(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(httpx, "post", fake_post(calls))
    GeminiEmbedder("k", "gemini-embedding-001").embed_query("patent")
    request = calls[0][1]["requests"][0]
    assert request["taskType"] == "RETRIEVAL_QUERY"
    assert request["content"]["parts"][0]["text"] == "patent"

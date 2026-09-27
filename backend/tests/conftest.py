"""Shared test fixtures.

Tests never download models or call a real LLM: `FakeEmbedder` is a deterministic
bag-of-words embedder and `FakeLLM` returns scripted text. The corpus in
tests/fixtures/corpus is entirely FICTIONAL (widgets, moonflowers) — it is not law.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import zlib
from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services import Services, build_services

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus"
REPO_DATA = Path(__file__).resolve().parents[2] / "data"


class FakeEmbedder:
    """Hashes words into a fixed-size vector; texts sharing words get similar vectors."""

    model_name = "fake-bow"
    dim = 512

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for word in re.findall(r"\w+", text.lower()):
            if len(word) > 2:
                vector[zlib.crc32(word.encode()) % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts):
        return [self._vector(t) for t in texts]

    def embed_query(self, text):
        return self._vector(text)


Responder = Callable[[str, str, dict], str]

DEFAULT_ANSWER = "Widgets must be registered with the registrar. [S1]"


def statement_ids(user_prompt: str) -> list[int]:
    """Statement numbers listed in a verification prompt."""
    statements = user_prompt.split("STATEMENTS:", 1)[-1]
    return [int(n) for n in re.findall(r"^(\d+)\. ", statements, flags=re.MULTILINE)]


def verification_json(user_prompt: str, unsupported: set[int] = frozenset(), on_point: bool = True) -> str:
    results = [{"id": i, "supported": i not in unsupported} for i in statement_ids(user_prompt)]
    return json.dumps({"on_point": on_point, "results": results})


def routing_responder(scope: str = "in_scope", intents: list[str] | None = None, unsupported: set[int] = frozenset()):
    """JSON responder answering router calls with a fixed route and fact-checks with `unsupported`."""

    def respond(system: str, user: str, kwargs: dict) -> str:
        if "route user messages" in system:
            return json.dumps({"scope": scope, "intents": intents or [], "search_query": user.split(":", 1)[-1]})
        return verification_json(user, unsupported)

    return respond


class FakeLLM:
    """Scripted LLM. `answer` is returned for drafting calls; JSON-mode calls get `json_responder`
    (default: the fact-check marks every statement supported)."""

    provider = "fake"
    model = "fake-model"

    def __init__(
        self,
        answer: str | Responder = DEFAULT_ANSWER,
        json_responder: Responder | None = None,
    ) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.answer = answer
        self.json_responder = json_responder or (lambda system, user, kw: verification_json(user))

    def complete(self, system: str, user: str, **kwargs) -> str:
        self.calls.append((system, user, kwargs))
        if kwargs.get("json_mode"):
            return self.json_responder(system, user, kwargs)
        return self.answer(system, user, kwargs) if callable(self.answer) else self.answer


class FakeReranker:
    """Scores a chunk by the share of query words it contains."""

    def score(self, query, texts):
        words = set(re.findall(r"\w{3,}", query.lower()))
        return [len(words & set(re.findall(r"\w{3,}", t.lower()))) / max(len(words), 1) for t in texts]


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    target = tmp_path / "data"
    shutil.copytree(FIXTURE_CORPUS, target)
    # The real (non-legal) configuration files: classifier questions and the curated links list
    for name in ("formulation_flow.yaml", "registry_links.yaml"):
        shutil.copy(REPO_DATA / name, target / name)
    return target


@pytest.fixture
def settings(tmp_path: Path, data_dir: Path) -> Settings:
    return Settings(
        _env_file=None,
        data_dir=data_dir,
        storage_dir=tmp_path / "storage",
        llm_provider="none",
        admin_mode=False,
        log_queries=True,
        retrieval_top_k=4,
        # FakeEmbedder similarities are low; scale them like a real model's range
        similarity_floor=0.0,
        similarity_ceiling=0.4,
    )


@pytest.fixture
def make_services(settings: Settings):
    def _make(llm=None, ingest: bool = True, reranker=None, **overrides) -> Services:
        s = settings.model_copy(update=overrides) if overrides else settings
        services = build_services(s, embedder=FakeEmbedder(), llm=llm, reranker=reranker)
        if ingest:
            services.ingestor().ingest()
        return services

    return _make


@pytest.fixture
def make_client(make_services):
    def _make(llm=None, **overrides) -> tuple[TestClient, Services]:
        services = make_services(llm=llm, **overrides)
        return TestClient(create_app(services)), services

    return _make

"""Shared test fixtures.

Tests never download models or call a real LLM: `FakeEmbedder` is a deterministic
bag-of-words embedder and `FakeLLM` returns scripted text. The corpus in
tests/fixtures/corpus is entirely FICTIONAL (widgets, moonflowers) — it is not law.
"""

from __future__ import annotations

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


class FakeLLM:
    provider = "fake"
    model = "fake-model"

    def __init__(self, responder: Responder | None = None) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.responder = responder or (lambda system, user, kw: "Widgets must be registered with the registrar. [S1]")

    def complete(self, system: str, user: str, **kwargs) -> str:
        self.calls.append((system, user, kwargs))
        return self.responder(system, user, kwargs)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    target = tmp_path / "data"
    shutil.copytree(FIXTURE_CORPUS, target)
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
    )


@pytest.fixture
def make_services(settings: Settings):
    def _make(llm=None, ingest: bool = True, **overrides) -> Services:
        s = settings.model_copy(update=overrides) if overrides else settings
        services = build_services(s, embedder=FakeEmbedder(), llm=llm)
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

"""Builds the object graph once at startup. Tests pass fakes (embedder, LLM, reranker) into `build_services`."""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.agents.grounded import GroundedAnswerer
from app.agents.orchestrator import ChatService
from app.config import Settings
from app.db.audit import AuditLog
from app.db.repository import CorpusRepository
from app.db.session import SessionFactory, make_session_factory
from app.ingest.pipeline import Ingestor
from app.llm.base import LLMClient
from app.llm.factory import build_llm
from app.retrieval.bm25 import BM25Search
from app.retrieval.embeddings import Embedder, SentenceTransformerEmbedder
from app.retrieval.reranker import CrossEncoderReranker, Reranker
from app.retrieval.search import Retriever, default_similarity_range
from app.retrieval.vector_store import VectorStore

_UNSET = object()


@dataclass
class Services:
    settings: Settings
    session_factory: SessionFactory
    repository: CorpusRepository
    embedder: Embedder
    vector_store: VectorStore
    retriever: Retriever
    llm: LLMClient | None
    audit: AuditLog
    answerer: GroundedAnswerer
    chat: ChatService

    def ingestor(self) -> Ingestor:
        return Ingestor(self.settings, self.session_factory, self.vector_store, self.embedder)


def build_services(
    settings: Settings,
    *,
    embedder: Embedder | None = None,
    llm=_UNSET,
    reranker: Reranker | None | object = _UNSET,
) -> Services:
    if settings.hf_disable_xet:
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    session_factory = make_session_factory(settings.sqlite_path)
    repository = CorpusRepository(session_factory)
    embedder = embedder or SentenceTransformerEmbedder(settings.embedding_model, settings.embedding_device)
    vector_store = VectorStore(settings.chroma_dir, embedder.model_name)

    if reranker is _UNSET:
        reranker = (
            CrossEncoderReranker(settings.reranker_model, settings.embedding_device)
            if settings.reranker_enabled
            else None
        )
    floor, ceiling = default_similarity_range(embedder.model_name)
    retriever = Retriever(
        repository,
        vector_store,
        embedder,
        bm25=BM25Search(repository),
        reranker=reranker,  # type: ignore[arg-type]
        top_k=settings.retrieval_top_k,
        candidates=settings.retrieval_candidates,
        similarity_range=(
            settings.similarity_floor if settings.similarity_floor is not None else floor,
            settings.similarity_ceiling if settings.similarity_ceiling is not None else ceiling,
        ),
    )
    llm_client = build_llm(settings) if llm is _UNSET else llm
    audit = AuditLog(session_factory, enabled=settings.log_queries)
    answerer = GroundedAnswerer(
        retriever, llm_client, threshold=settings.confidence_threshold, verify=settings.citation_verification
    )
    chat = ChatService(settings, answerer, audit)
    return Services(
        settings=settings,
        session_factory=session_factory,
        repository=repository,
        embedder=embedder,
        vector_store=vector_store,
        retriever=retriever,
        llm=llm_client,
        audit=audit,
        answerer=answerer,
        chat=chat,
    )

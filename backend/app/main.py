"""FastAPI application: wires settings, services and routes."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.ingest.loaders import SUPPORTED_SUFFIXES
from app.ingest.manifest import ManifestError, load_manifest
from app.guardrails.messages import msg
from app.guardrails.pii import scrub
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CorpusStatus,
    EscalateRequest,
    EscalateResponse,
    HealthResponse,
    LlmStatus,
    SourcesResponse,
)
from app.services import Services, build_services
from app.sources import list_sources

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def get_services(request: Request) -> Services:
    return request.app.state.services


def create_app(services: Services | None = None) -> FastAPI:
    settings = services.settings if services else get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "services", None) is None:
            app.state.services = build_services(settings)
        yield

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.state.services = services  # injected services (tests) are available without running lifespan
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    def health(svc: Services = Depends(get_services)) -> HealthResponse:
        """Liveness check plus a summary of how the service is configured."""
        raw_dir = svc.settings.raw_dir
        raw_files = (
            sum(1 for p in raw_dir.rglob("*") if p.suffix.lower() in SUPPORTED_SUFFIXES) if raw_dir.exists() else 0
        )
        try:
            manifest_entries = len(load_manifest(svc.settings.manifest_path))
        except ManifestError:
            manifest_entries = 0
        documents, chunks = svc.repository.corpus_counts()
        return HealthResponse(
            status="ok",
            app=svc.settings.app_name,
            version=svc.settings.app_version,
            llm=LlmStatus(
                provider=svc.settings.llm_provider,
                model=svc.settings.llm_model,
                configured=svc.llm is not None,
            ),
            embedding_model=svc.embedder.model_name,
            corpus=CorpusStatus(
                raw_files=raw_files, manifest_entries=manifest_entries, documents=documents, chunks=chunks
            ),
        )

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest, svc: Services = Depends(get_services)) -> ChatResponse:
        """Answer a question with cited, per-jurisdiction blocks."""
        return await run_in_threadpool(svc.chat.handle, body)

    @app.post("/api/escalate", response_model=EscalateResponse)
    def escalate(body: EscalateRequest, svc: Services = Depends(get_services)) -> EscalateResponse:
        """Record a request for a human IP facilitator. Nothing is sent anywhere; it appears on the admin page."""
        escalation_id = svc.audit.record_escalation(
            session_id=body.session_id,
            query_id=body.query_id,
            jurisdiction=body.jurisdiction,
            language=body.language,
            scrubbed_note=scrub(body.note).text,
        )
        reference = f"ESC-{escalation_id:05d}"
        return EscalateResponse(
            status="recorded", reference=reference, message=msg("escalation_recorded", body.language).format(reference=reference)
        )

    @app.get("/api/sources", response_model=SourcesResponse)
    def sources(svc: Services = Depends(get_services)) -> SourcesResponse:
        """Corpus documents with their versions and ingestion status."""
        return list_sources(svc.settings, svc.repository)

    return app


app = create_app()

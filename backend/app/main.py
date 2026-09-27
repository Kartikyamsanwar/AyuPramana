"""FastAPI application: wires settings, middleware and routes."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import CorpusStatus, HealthResponse, LlmStatus

RAW_SUFFIXES = {".pdf", ".html", ".htm", ".txt", ".md"}


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        """Liveness check plus a summary of how the service is configured."""
        raw_files = (
            sum(1 for p in settings.raw_dir.rglob("*") if p.suffix.lower() in RAW_SUFFIXES)
            if settings.raw_dir.exists()
            else 0
        )
        return HealthResponse(
            status="ok",
            app=settings.app_name,
            version=settings.app_version,
            llm=LlmStatus(
                provider=settings.llm_provider,
                model=settings.llm_model,
                configured=settings.llm_configured,
            ),
            embedding_model=settings.embedding_model,
            corpus=CorpusStatus(raw_files=raw_files),
        )

    return app


app = create_app()

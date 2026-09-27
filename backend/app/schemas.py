"""Request and response models shared by the API routes."""

from __future__ import annotations

from pydantic import BaseModel


class LlmStatus(BaseModel):
    provider: str
    model: str
    configured: bool


class CorpusStatus(BaseModel):
    raw_files: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    llm: LlmStatus
    embedding_model: str
    corpus: CorpusStatus

"""Application settings.

All tunable values are read once from environment variables and the repo-root
`.env` file (see `.env.example`). Nothing else in the code reads the
environment directly, so this file is the single place to look for a knob.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parents[2] is the repository root (also true inside Docker: /app)
REPO_ROOT = Path(__file__).resolve().parents[2]

LlmProvider = Literal["groq", "anthropic", "ollama", "none"]


class Settings(BaseSettings):
    """Typed view of `.env`. Field names map to UPPER_CASE environment variables."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,  # "KEY=" in .env means "use the default"
        extra="ignore",
    )

    app_name: str = "AyuPramana"
    app_version: str = "0.1.0"

    # --- LLM ---------------------------------------------------------------
    llm_provider: LlmProvider = "groq"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"
    groq_fast_model: str = "openai/gpt-oss-20b"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    anthropic_fast_model: str = "claude-haiku-4-5-20251001"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2:3b"
    ollama_fast_model: str = ""
    llm_reasoning_effort: Literal["low", "medium", "high"] = "low"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 4

    # --- Embeddings and retrieval ------------------------------------------
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    # Some networks stall Hugging Face's Xet downloads at 0 bytes; true = use plain HTTPS downloads
    hf_disable_xet: bool = False
    reranker_enabled: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    retrieval_top_k: int = 6
    retrieval_candidates: int = 30
    # Map raw cosine similarity to 0-1 relevance; blank = sensible default for the model
    similarity_floor: float | None = None
    similarity_ceiling: float | None = None
    chunk_target_tokens: int = 600
    chunk_max_tokens: int = 800
    chunk_overlap_tokens: int = 60

    # --- Guardrails --------------------------------------------------------
    confidence_threshold: float = 0.55
    citation_verification: bool = True

    # --- Translation -------------------------------------------------------
    bhashini_user_id: str = ""
    bhashini_api_key: str = ""
    bhashini_pipeline_id: str = ""
    bhashini_config_url: str = (
        "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    )

    # --- Storage -----------------------------------------------------------
    data_dir: Path = REPO_ROOT / "data"
    storage_dir: Path = REPO_ROOT / "storage"
    # Built web UI (frontend/dist) to serve from the backend in single-container hosting; unset in development
    static_dir: Path | None = None

    # --- Privacy and admin -------------------------------------------------
    admin_mode: bool = False
    log_queries: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("data_dir", "storage_dir", "static_dir", mode="after")
    @classmethod
    def _resolve_from_repo_root(cls, value: Path | None) -> Path | None:
        """Relative paths in `.env` are taken relative to the repository root."""
        if value is None:
            return None
        return value if value.is_absolute() else (REPO_ROOT / value).resolve()

    # --- Derived values ----------------------------------------------------
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "manifest.yaml"

    @property
    def sqlite_path(self) -> Path:
        return self.storage_dir / "ayupramana.db"

    @property
    def chroma_dir(self) -> Path:
        return self.storage_dir / "chroma"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_model(self) -> str:
        """Name of the main model for the configured provider."""
        return {
            "groq": self.groq_model,
            "anthropic": self.anthropic_model,
            "ollama": self.ollama_model,
            "none": "",
        }[self.llm_provider]

    @property
    def llm_configured(self) -> bool:
        """True when the chosen provider has what it needs to be called."""
        if self.llm_provider == "groq":
            return bool(self.groq_api_key)
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return self.llm_provider == "ollama"

    @property
    def bhashini_configured(self) -> bool:
        return bool(self.bhashini_user_id and self.bhashini_api_key and self.bhashini_pipeline_id)


@lru_cache
def get_settings() -> Settings:
    """Settings are loaded once per process."""
    return Settings()

"""Build the configured LLM client (or None when no LLM is available)."""

from __future__ import annotations

from app.config import Settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.base import LLMClient
from app.llm.openai_compat import OpenAICompatibleClient


def build_llm(settings: Settings) -> LLMClient | None:
    """Return a client for LLM_PROVIDER, or None if it is 'none' or its API key is missing.

    With no LLM the assistant still works in a safe "extractive" mode: it shows the
    retrieved provisions verbatim instead of writing an answer.
    """
    if not settings.llm_configured:
        return None
    if settings.llm_provider == "groq":
        return OpenAICompatibleClient(
            provider="groq",
            base_url=settings.groq_base_url,
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            fast_model=settings.groq_fast_model,
            reasoning_effort=settings.llm_reasoning_effort,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    if settings.llm_provider == "ollama":
        return OpenAICompatibleClient(
            provider="ollama",
            base_url=settings.ollama_base_url,
            api_key="",
            model=settings.ollama_model,
            fast_model=settings.ollama_fast_model,
            reasoning_effort=settings.llm_reasoning_effort,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    if settings.llm_provider == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            fast_model=settings.anthropic_fast_model,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    return None

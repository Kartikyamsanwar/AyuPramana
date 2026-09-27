"""The provider-agnostic LLM interface used by every agent."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol


class LLMError(RuntimeError):
    """The LLM could not be reached or returned something unusable. Callers fall back safely."""


class LLMClient(Protocol):
    provider: str
    model: str

    def complete(
        self,
        system: str,
        user: str,
        *,
        fast: bool = False,
        json_mode: bool = False,
        max_tokens: int = 1500,
        temperature: float = 0.0,
    ) -> str:
        """Single-turn completion. `fast=True` uses the cheaper routing model."""
        ...


def parse_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from model output (tolerates ```json fences and chatter)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("LLM did not return JSON") from None
        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM returned invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LLMError("LLM returned JSON that is not an object")
    return value

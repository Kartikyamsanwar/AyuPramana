"""Client for the Anthropic Messages API (optional provider)."""

from __future__ import annotations

import logging
import time

import httpx

from app.llm.base import LLMError

log = logging.getLogger(__name__)

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AnthropicClient:
    provider = "anthropic"

    def __init__(self, api_key: str, model: str, fast_model: str = "", timeout: float = 60.0, max_retries: int = 3):
        self.model = model
        self.fast_model = fast_model or model
        self._headers = {"x-api-key": api_key, "anthropic-version": API_VERSION}
        self._timeout = timeout
        self._max_retries = max_retries

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
        if json_mode:
            system += "\n\nRespond with a single JSON object and nothing else."
        payload = {
            "model": self.fast_model if fast else self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        last_error = "unknown error"
        for attempt in range(self._max_retries + 1):
            try:
                response = httpx.post(API_URL, json=payload, headers=self._headers, timeout=self._timeout)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code == 200:
                    blocks = response.json().get("content", [])
                    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
                    if not text.strip():
                        raise LLMError("anthropic: empty response")
                    return text
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
                if response.status_code not in {429, 500, 502, 503, 504, 529}:
                    break
            if attempt < self._max_retries:
                time.sleep(min(2**attempt, 10))
        log.warning("anthropic call failed: %s", last_error)
        raise LLMError(f"anthropic: {last_error}")

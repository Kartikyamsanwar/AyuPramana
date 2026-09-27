"""Client for OpenAI-compatible chat APIs — used for both Groq (cloud) and Ollama (local)."""

from __future__ import annotations

import logging
import time

import httpx

from app.llm.base import LLMError

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class OpenAICompatibleClient:
    def __init__(
        self,
        provider: str,
        base_url: str,
        api_key: str,
        model: str,
        fast_model: str = "",
        reasoning_effort: str = "low",
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.provider = provider
        self.model = model
        self.fast_model = fast_model or model
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._reasoning_effort = reasoning_effort
        self._timeout = timeout
        self._max_retries = max_retries

    def _payload(self, model: str, system: str, user: str, json_mode: bool, max_tokens: int, temperature: float) -> dict:
        payload: dict = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
        }
        # Groq names the limit max_completion_tokens; Ollama still expects max_tokens
        payload["max_completion_tokens" if self.provider == "groq" else "max_tokens"] = max_tokens
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if "gpt-oss" in model:
            # Reasoning models: keep thinking short and out of the returned content
            payload["reasoning_effort"] = self._reasoning_effort
            if self.provider == "groq":
                payload["include_reasoning"] = False
        return payload

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
        model = self.fast_model if fast else self.model
        payload = self._payload(model, system, user, json_mode, max_tokens, temperature)
        last_error = "unknown error"
        for attempt in range(self._max_retries + 1):
            try:
                response = httpx.post(self._url, json=payload, headers=self._headers, timeout=self._timeout)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code == 200:
                    try:
                        content = response.json()["choices"][0]["message"].get("content") or ""
                    except (ValueError, KeyError, IndexError) as exc:
                        raise LLMError(f"{self.provider}: unexpected response shape") from exc
                    if not content.strip():
                        raise LLMError(f"{self.provider}: empty response")
                    return content
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
                if response.status_code not in RETRYABLE_STATUS:
                    break
                retry_after = response.headers.get("retry-after")
                if retry_after and attempt < self._max_retries:
                    time.sleep(min(float(retry_after) + 0.5, 30.0))
                    continue
            if attempt < self._max_retries:
                time.sleep(min(2**attempt, 10))
        log.warning("%s call failed: %s", self.provider, last_error)
        raise LLMError(f"{self.provider}: {last_error}")

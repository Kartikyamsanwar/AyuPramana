"""Bhashini (MeitY ULCA) translation.

Two calls, as documented by Bhashini:
1. pipeline *config* call (userID + ulcaApiKey) → the inference endpoint, its auth header and the serviceId
2. pipeline *compute* call to that endpoint → translations
The config result is cached per language pair.
"""

from __future__ import annotations

import logging
import threading
from typing import Sequence

import httpx

from app.translate.base import TranslationError, translate_markdown_by_segments

log = logging.getLogger(__name__)


class BhashiniTranslator:
    name = "bhashini"

    def __init__(self, user_id: str, api_key: str, pipeline_id: str, config_url: str, timeout: float = 30.0) -> None:
        self._user_id = user_id
        self._api_key = api_key
        self._pipeline_id = pipeline_id
        self._config_url = config_url
        self._timeout = timeout
        self._configs: dict[tuple[str, str], tuple[str, dict[str, str], str]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _task(source: str, target: str, service_id: str | None = None) -> dict:
        config: dict = {"language": {"sourceLanguage": source, "targetLanguage": target}}
        if service_id:
            config["serviceId"] = service_id
        return {"taskType": "translation", "config": config}

    def _endpoint(self, source: str, target: str) -> tuple[str, dict[str, str], str]:
        with self._lock:
            cached = self._configs.get((source, target))
        if cached:
            return cached
        try:
            response = httpx.post(
                self._config_url,
                json={
                    "pipelineTasks": [self._task(source, target)],
                    "pipelineRequestConfig": {"pipelineId": self._pipeline_id},
                },
                headers={"userID": self._user_id, "ulcaApiKey": self._api_key},
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
            endpoint = data["pipelineInferenceAPIEndPoint"]
            auth = endpoint["inferenceApiKey"]
            service_id = data["pipelineResponseConfig"][0]["config"][0]["serviceId"]
            result = (endpoint["callbackUrl"], {auth["name"]: auth["value"]}, service_id)
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise TranslationError(f"Bhashini config call failed: {exc}") from exc
        with self._lock:
            self._configs[(source, target)] = result
        return result

    def translate_texts(self, texts: Sequence[str], source: str, target: str) -> list[str]:
        if not texts:
            return []
        url, headers, service_id = self._endpoint(source, target)
        try:
            response = httpx.post(
                url,
                json={
                    "pipelineTasks": [self._task(source, target, service_id)],
                    "inputData": {"input": [{"source": text} for text in texts]},
                },
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            outputs = response.json()["pipelineResponse"][0]["output"]
            return [item["target"] for item in outputs]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise TranslationError(f"Bhashini compute call failed: {exc}") from exc

    def translate_markdown(self, markdown: str, source: str, target: str) -> str:
        return translate_markdown_by_segments(self, markdown, source, target)

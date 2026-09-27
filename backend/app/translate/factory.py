"""Choose the translator: Bhashini when configured (with the LLM as fallback), else the LLM, else none."""

from __future__ import annotations

import logging
from typing import Sequence

from app.config import Settings
from app.llm.base import LLMClient
from app.translate.base import TranslationError, Translator
from app.translate.bhashini import BhashiniTranslator
from app.translate.llm_translate import LLMTranslator

log = logging.getLogger(__name__)


class FallbackTranslator:
    """Try each translator in order; the first that succeeds wins."""

    def __init__(self, translators: list[Translator]) -> None:
        self.translators = translators
        self.name = "+".join(t.name for t in translators)

    def _try(self, method: str, *args):
        errors = []
        for translator in self.translators:
            try:
                return getattr(translator, method)(*args)
            except TranslationError as exc:
                log.warning("%s translation failed: %s", translator.name, exc)
                errors.append(f"{translator.name}: {exc}")
        raise TranslationError("; ".join(errors) or "no translator available")

    def translate_texts(self, texts: Sequence[str], source: str, target: str) -> list[str]:
        return self._try("translate_texts", texts, source, target)

    def translate_markdown(self, markdown: str, source: str, target: str) -> str:
        return self._try("translate_markdown", markdown, source, target)


def build_translator(settings: Settings, llm: LLMClient | None) -> Translator | None:
    chain: list[Translator] = []
    if settings.bhashini_configured:
        chain.append(
            BhashiniTranslator(
                settings.bhashini_user_id,
                settings.bhashini_api_key,
                settings.bhashini_pipeline_id,
                settings.bhashini_config_url,
            )
        )
    if llm is not None:
        chain.append(LLMTranslator(llm))
    if not chain:
        return None
    return chain[0] if len(chain) == 1 else FallbackTranslator(chain)

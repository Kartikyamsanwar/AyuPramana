"""LLM-based translation — the fallback when Bhashini isn't configured or fails."""

from __future__ import annotations

import json
from typing import Sequence

from app.llm.base import LLMClient, LLMError, parse_json_object
from app.translate.base import LANGUAGE_NAMES, TranslationError, check_markers

MARKDOWN_SYSTEM = """You translate legal-information text for Ayurveda practitioners and businesses.
Translate the user's Markdown from {source} into {target}.
Rules:
- Keep all Markdown formatting (headings, bullets, bold, links).
- Keep every citation marker such as [S1] exactly as written, at the end of the same sentence.
- Keep URLs unchanged. Keep names of Acts, treaties and section/article/rule numbers in their official English form; you may add the {target} term in brackets after them.
- Do not add, remove or explain anything. Output only the translation."""

TEXTS_SYSTEM = """Translate each string in the JSON list from {source} into {target}. Keep names of laws and section numbers in English.
Return JSON only: {{"translations": ["...", "..."]}} with exactly one translation per input, in the same order."""


class LLMTranslator:
    name = "llm"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def translate_texts(self, texts: Sequence[str], source: str, target: str) -> list[str]:
        if not texts:
            return []
        system = TEXTS_SYSTEM.format(source=LANGUAGE_NAMES[source], target=LANGUAGE_NAMES[target])
        try:
            data = parse_json_object(
                self.llm.complete(system, json.dumps(list(texts), ensure_ascii=False), fast=True, json_mode=True)
            )
        except LLMError as exc:
            raise TranslationError(str(exc)) from exc
        translations = data.get("translations")
        if not isinstance(translations, list) or len(translations) != len(texts):
            raise TranslationError("LLM returned the wrong number of translations")
        return [str(t) for t in translations]

    def translate_markdown(self, markdown: str, source: str, target: str) -> str:
        system = MARKDOWN_SYSTEM.format(source=LANGUAGE_NAMES[source], target=LANGUAGE_NAMES[target])
        try:
            translated = self.llm.complete(system, markdown, max_tokens=2500).strip()
        except LLMError as exc:
            raise TranslationError(str(exc)) from exc
        check_markers(markdown, translated)
        return translated

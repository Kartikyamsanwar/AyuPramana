"""Translator interface plus the helpers every implementation shares.

English is the pivot language: a Hindi/Marathi question is translated to English for
routing and retrieval (the corpus is English), and generated answers are translated back.
Citation markers like [S2] must survive translation unchanged, so every translation is
checked, and a translation that loses or invents markers is rejected.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Protocol, Sequence

MARKER_RE = re.compile(r"\[S\d+\]")
_MARKER_GROUP_RE = re.compile(r"(?:\s*\[S\d+\])+")
_PREFIX_RE = re.compile(r"^(\s*(?:#{1,6}\s+|[-*+]\s+(?:\[[ xX]\]\s+)?|\d+[.)]\s+)?)")
_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}


class TranslationError(RuntimeError):
    pass


class Translator(Protocol):
    name: str

    def translate_texts(self, texts: Sequence[str], source: str, target: str) -> list[str]:
        """Translate plain-text segments (no Markdown)."""
        ...

    def translate_markdown(self, markdown: str, source: str, target: str) -> str:
        """Translate Markdown, keeping formatting and [S#] markers."""
        ...


def has_devanagari(text: str) -> bool:
    return bool(_DEVANAGARI_RE.search(text))


def check_markers(original: str, translated: str) -> None:
    if Counter(MARKER_RE.findall(original)) != Counter(MARKER_RE.findall(translated)):
        raise TranslationError("translation changed the citation markers")


def translate_markdown_by_segments(translator: Translator, markdown: str, source: str, target: str) -> str:
    """For plain-text engines (e.g. Bhashini): translate each line's text between citation markers,
    keeping list/heading prefixes, markers and link lines exactly as they were."""
    jobs: list[tuple[int, int, int]] = []  # (line index, start, end) of text to translate
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if not line.strip() or "](http" in line:
            continue  # blank lines and link lists stay as they are
        position = _PREFIX_RE.match(line).end()
        for match in _MARKER_GROUP_RE.finditer(line, position):
            if line[position : match.start()].strip():
                jobs.append((index, position, match.start()))
            position = match.end()
        if line[position:].strip():
            jobs.append((index, position, len(line)))
    if not jobs:
        return markdown
    sources = [lines[i][start:end].strip() for i, start, end in jobs]
    translated = translator.translate_texts(sources, source, target)
    if len(translated) != len(sources):
        raise TranslationError("translator returned a different number of segments")
    for (index, start, end), text in sorted(zip(jobs, translated), key=lambda item: (item[0][0], -item[0][1])):
        line = lines[index]
        segment = line[start:end]
        leading = segment[: len(segment) - len(segment.lstrip())]  # keep the space after a previous marker
        trailing = " " if end < len(line) else ""
        lines[index] = f"{line[:start]}{leading}{text.strip()}{trailing}{line[end:].lstrip()}"
    result = "\n".join(lines)
    check_markers(markdown, result)
    return result

"""Parse and renumber [S1]-style citation markers in LLM output."""

from __future__ import annotations

import re
from typing import Sequence, TypeVar

T = TypeVar("T")

MARKER_RE = re.compile(r"\[S(\d+)\]")
# Variants models produce: "[ S2 ]", "[s2]", "[S 2]", "【S2】", "【S1†L1-L4】", "[S1, S3]", "[S1; S3]"
_LOOSE_RE = re.compile(r"[\[【]\s*([Ss]\s*\d+(?:\s*[,;]\s*[Ss]?\s*\d+)*)(?:\s*†[^\]】]*)?\s*[\]】]")


def normalize_markers(text: str) -> str:
    """Normalise every marker variant to the one shape "[S1][S3]"."""

    def repl(match: re.Match[str]) -> str:
        numbers = re.findall(r"\d+", match.group(1))
        return "".join(f"[S{n}]" for n in numbers)

    return _LOOSE_RE.sub(repl, text)


def renumber_citations(markdown: str, sources: Sequence[T]) -> tuple[str, list[T]]:
    """Keep only markers that point at a real source and renumber them 1..n in order of first use.

    Returns the rewritten markdown and the list of cited sources (index i ↔ marker [S{i+1}]).
    Markers pointing outside `sources` are removed (the model must not cite what it wasn't given).
    """
    markdown = normalize_markers(markdown)
    mapping: dict[int, int] = {}
    cited: list[T] = []

    def repl(match: re.Match[str]) -> str:
        original = int(match.group(1))
        if not 1 <= original <= len(sources):
            return ""
        if original not in mapping:
            cited.append(sources[original - 1])
            mapping[original] = len(cited)
        return f"[S{mapping[original]}]"

    rewritten = MARKER_RE.sub(repl, markdown)
    # Collapse duplicate adjacent markers like [S1][S1]
    rewritten = re.sub(r"(\[S\d+\])(?:\1)+", r"\1", rewritten)
    return rewritten.strip(), cited


def shift_markers(markdown: str, mapping: dict[int, int]) -> str:
    """Rewrite marker numbers using `mapping` (old → new). Used when merging several answers."""
    return MARKER_RE.sub(lambda m: f"[S{mapping.get(int(m.group(1)), int(m.group(1)))}]", markdown)

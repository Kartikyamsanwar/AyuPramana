"""The result every specialist agent returns."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.retrieval.search import RetrievedChunk


@dataclass
class SpecialistResult:
    """`citations[i]` is the source behind marker [S{i+1}] in `answer_markdown`."""

    jurisdiction: str
    answer_markdown: str
    citations: list[RetrievedChunk]
    confidence: float
    abstained: bool
    abstain_reason: str | None = None
    mode: str = "generated"  # generated | extractive | abstained
    agent: str = "general"
    retrieved: list[RetrievedChunk] = field(default_factory=list)  # everything retrieved (for eval/debug)
    signals: dict[str, float] = field(default_factory=dict)  # confidence components, for audit

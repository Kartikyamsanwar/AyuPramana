"""Shared pieces for specialist agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from app.agents.types import SpecialistResult

EventSink = Callable[[str, dict], None]


def _ignore(event: str, data: dict) -> None:
    return None


@dataclass
class TurnContext:
    """Everything a specialist needs about the current question."""

    question: str  # English, PII-scrubbed
    search_query: str  # retrieval-friendly rewrite (router)
    language: str = "en"
    session_id: str = ""
    emit: EventSink = field(default=_ignore)  # progress events for streaming


class Specialist(Protocol):
    name: str

    def run(self, ctx: TurnContext, jurisdiction: str) -> SpecialistResult:
        """Return {answer_markdown, citations[], confidence, abstained} for one jurisdiction."""
        ...

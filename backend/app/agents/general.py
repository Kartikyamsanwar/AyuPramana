"""General regulatory Q&A: the default specialist for in-scope questions no other specialist owns."""

from __future__ import annotations

from app.agents.base import TurnContext
from app.agents.grounded import GroundedAnswerer
from app.agents.types import SpecialistResult


class GeneralAgent:
    name = "general_regulatory"

    def __init__(self, answerer: GroundedAnswerer) -> None:
        self.answerer = answerer

    def run(self, ctx: TurnContext, jurisdiction: str) -> SpecialistResult:
        return self.answerer.answer(
            ctx.question, jurisdiction, agent=self.name, retrieval_query=ctx.search_query, emit=ctx.emit
        )

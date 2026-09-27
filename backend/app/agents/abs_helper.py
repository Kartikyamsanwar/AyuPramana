"""ABS Compliance helper: a cited checklist of access-and-benefit-sharing obligations."""

from __future__ import annotations

from app.agents.base import TurnContext
from app.agents.grounded import GroundedAnswerer
from app.agents.types import SpecialistResult

TASK = (
    "The user plans to use biological resources and/or associated traditional knowledge. First, in one sentence, say "
    "when the obligations in the SOURCES apply. Then give a compliance checklist as Markdown task items "
    "('- [ ] ...'), one obligation per item (for example prior approval, information to provide, benefit sharing), "
    "each ending with its citation marker. Include only obligations stated in the SOURCES."
)


class ABSComplianceAgent:
    name = "abs_compliance"

    def __init__(self, answerer: GroundedAnswerer) -> None:
        self.answerer = answerer

    def run(self, ctx: TurnContext, jurisdiction: str) -> SpecialistResult:
        return self.answerer.answer(
            ctx.question,
            jurisdiction,
            domains=["abs", "tk"],
            task=TASK,
            agent=self.name,
            retrieval_query=f"access benefit sharing approval biological resources traditional knowledge {ctx.search_query}",
            emit=ctx.emit,
        )

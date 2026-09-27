"""IP Routing agent: which IP rights (patent, trade mark, GI, design, copyright, plant variety) fit the situation."""

from __future__ import annotations

from app.agents.base import TurnContext
from app.agents.grounded import GroundedAnswerer
from app.agents.types import SpecialistResult

TASK = (
    "Explain which intellectual-property rights (for example patent, trade mark, geographical indication, design, "
    "copyright or plant variety protection) the SOURCES show could apply to the user's situation: what each "
    "protects and its key conditions or exclusions. Only mention rights that the SOURCES cover."
)


class IPRoutingAgent:
    name = "ip_protection"

    def __init__(self, answerer: GroundedAnswerer) -> None:
        self.answerer = answerer

    def run(self, ctx: TurnContext, jurisdiction: str) -> SpecialistResult:
        return self.answerer.answer(
            ctx.question,
            jurisdiction,
            domains=["ip", "tk"],
            task=TASK,
            agent=self.name,
            retrieval_query=ctx.search_query,
            emit=ctx.emit,
        )

"""Registry navigator: maps the user's goal to the right office / portal / form.

The procedural explanation is grounded in retrieved rules (cited). Links come only
from data/registry_links.yaml entries the team has marked `verified: true`, plus the
official source URLs already recorded in the manifest (shown on citations).
"""

from __future__ import annotations

from pathlib import Path

from app.agents.base import TurnContext
from app.agents.grounded import GroundedAnswerer
from app.agents.registry_links import links_markdown, load_registry_links, topics_for, verified_links
from app.agents.types import SpecialistResult
from app.guardrails.messages import msg

TASK = (
    "Explain what the SOURCES say about the application procedure for what the user wants to do: who applies, "
    "to which authority or office (only if the SOURCES name it), and what must be submitted. "
    "Do not invent form numbers, fees, time limits or web addresses."
)


class RegistryNavigatorAgent:
    name = "registry_navigation"

    def __init__(self, answerer: GroundedAnswerer, registry_path: Path) -> None:
        self.answerer = answerer
        self.registry_path = registry_path

    def run(self, ctx: TurnContext, jurisdiction: str, intents: list[str] | None = None) -> SpecialistResult:
        result = self.answerer.answer(
            ctx.question,
            jurisdiction,
            task=TASK,
            agent=self.name,
            retrieval_query=f"application procedure registration authority {ctx.search_query}",
            emit=ctx.emit,
        )
        topics = topics_for(ctx.question, intents)
        links = verified_links(load_registry_links(self.registry_path), jurisdiction, topics)
        result.appendix = (
            links_markdown(links, msg("links_heading", ctx.language)) if links else msg("links_not_verified", ctx.language)
        )
        return result

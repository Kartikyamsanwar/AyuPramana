"""Prior-art / TKDL pointer: why traditional knowledge matters as prior art, plus links to official search portals.

It never scrapes or queries TKDL. The explanation comes from retrieved, cited
provisions; the portal links come only from the team-verified registry_links.yaml.
"""

from __future__ import annotations

from pathlib import Path

from app.agents.base import TurnContext
from app.agents.grounded import GroundedAnswerer
from app.agents.registry_links import links_markdown, load_registry_links, verified_links
from app.agents.types import SpecialistResult
from app.guardrails.messages import msg

TASK = (
    "Using only the SOURCES, explain why existing traditional knowledge matters as prior art: how it affects what "
    "counts as new or as an invention, and how documented traditional knowledge relates to examining patent "
    "applications or preventing misappropriation. Do not describe how to search any database."
)


class TKDLPointerAgent:
    name = "prior_art_tk"

    def __init__(self, answerer: GroundedAnswerer, registry_path: Path) -> None:
        self.answerer = answerer
        self.registry_path = registry_path

    def run(self, ctx: TurnContext, jurisdiction: str) -> SpecialistResult:
        result = self.answerer.answer(
            ctx.question,
            jurisdiction,
            domains=["tk", "ip"],
            task=TASK,
            agent=self.name,
            retrieval_query=f"traditional knowledge prior art novelty invention {ctx.search_query}",
            emit=ctx.emit,
        )
        links = verified_links(load_registry_links(self.registry_path), jurisdiction, {"prior_art_search", "tk"})
        result.appendix = (
            links_markdown(links, msg("links_heading", ctx.language)) if links else msg("links_not_verified", ctx.language)
        )
        return result

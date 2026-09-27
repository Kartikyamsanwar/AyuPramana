"""Grounded answering: retrieve → write an answer only from the sources → keep only valid citations.

Every specialist agent uses this. It never lets the LLM answer without sources, and if
the LLM is unavailable it falls back to quoting the retrieved provisions ("extractive" mode).
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.agents.citations import renumber_citations
from app.agents.prompts import GROUNDED_SYSTEM, grounded_user_prompt
from app.agents.types import SpecialistResult
from app.guardrails.messages import msg
from app.llm.base import LLMClient, LLMError
from app.retrieval.search import RetrievedChunk, Retriever

log = logging.getLogger(__name__)

INSUFFICIENT = "INSUFFICIENT_EVIDENCE"


def _snippet(text: str, limit: int = 220) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[:limit].rsplit(" ", 1)[0] + " …"


class GroundedAnswerer:
    def __init__(self, retriever: Retriever, llm: LLMClient | None) -> None:
        self.retriever = retriever
        self.llm = llm

    def answer(
        self,
        question: str,
        jurisdiction: str,
        *,
        domains: Sequence[str] | None = None,
        task: str = "",
        agent: str = "general",
        retrieval_query: str | None = None,
    ) -> SpecialistResult:
        retrieved = self.retriever.search(retrieval_query or question, jurisdiction, domains)
        if not retrieved:
            reason = "no_corpus" if self.retriever.repository.active_chunk_count(jurisdiction) == 0 else "no_sources"
            return self.abstain(jurisdiction, reason, agent, retrieved)

        if self.llm is None:
            return self.extractive(jurisdiction, retrieved, agent)
        try:
            draft = self.llm.complete(GROUNDED_SYSTEM, grounded_user_prompt(question, jurisdiction, retrieved, task))
        except LLMError as exc:
            log.warning("LLM unavailable, using extractive answer: %s", exc)
            return self.extractive(jurisdiction, retrieved, agent)

        if INSUFFICIENT in draft:
            return self.abstain(jurisdiction, "insufficient_evidence", agent, retrieved)
        markdown, cited = renumber_citations(draft, retrieved)
        if not cited:
            return self.abstain(jurisdiction, "no_citations", agent, retrieved)

        confidence = max(0.0, min(1.0, retrieved[0].relevance))
        return SpecialistResult(
            jurisdiction=jurisdiction,
            answer_markdown=markdown,
            citations=cited,
            confidence=confidence,
            abstained=False,
            agent=agent,
            retrieved=retrieved,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def abstain(
        jurisdiction: str, reason: str, agent: str, retrieved: list[RetrievedChunk], confidence: float = 0.0
    ) -> SpecialistResult:
        return SpecialistResult(
            jurisdiction=jurisdiction,
            answer_markdown="",
            citations=[],
            confidence=confidence,
            abstained=True,
            abstain_reason=reason,
            mode="abstained",
            agent=agent,
            retrieved=retrieved,
        )

    @staticmethod
    def extractive(jurisdiction: str, retrieved: list[RetrievedChunk], agent: str, limit: int = 3) -> SpecialistResult:
        """No LLM: quote the top provisions verbatim. Nothing is paraphrased, so nothing can be invented."""
        top = retrieved[:limit]
        lines = [msg("extractive_intro"), ""]
        for index, item in enumerate(top, start=1):
            c = item.chunk
            lines.append(f"- **{c.title} — {c.section_ref}:** “{_snippet(c.text)}” [S{index}]")
        return SpecialistResult(
            jurisdiction=jurisdiction,
            answer_markdown="\n".join(lines),
            citations=top,
            confidence=max(0.0, min(1.0, top[0].relevance)),
            abstained=False,
            mode="extractive",
            agent=agent,
            retrieved=retrieved,
        )

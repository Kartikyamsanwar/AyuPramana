"""Grounded answering, shared by every specialist agent.

    retrieve (hybrid, one jurisdiction)
      → draft an answer from the sources only (LLM)
      → keep only valid [S#] citations
      → fact-check each statement against its sources (citation verification)
      → confidence score → abstain if below threshold

If the LLM is unavailable, it falls back to quoting the retrieved provisions verbatim
("extractive" mode). Nothing is paraphrased in that mode, so nothing can be invented.
"""

from __future__ import annotations

import logging
from typing import Callable, Sequence

from app.agents.citations import renumber_citations
from app.agents.prompts import GROUNDED_SYSTEM, grounded_user_prompt
from app.agents.types import SpecialistResult
from app.guardrails import confidence as conf
from app.guardrails.messages import msg
from app.guardrails.verification import verify_answer
from app.llm.base import LLMClient, LLMError
from app.retrieval.search import RetrievedChunk, Retriever

log = logging.getLogger(__name__)

INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
MIN_SUPPORTED_FRACTION = 0.5
RELATED_LIMIT = 3


EventSink = Callable[[str, dict], None]


def _no_events(event: str, data: dict) -> None:
    return None


def _snippet(text: str, limit: int = 220) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[:limit].rsplit(" ", 1)[0] + " …"


class GroundedAnswerer:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLMClient | None,
        threshold: float = 0.55,
        verify: bool = True,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.threshold = threshold
        self.verify = verify

    def answer(
        self,
        question: str,
        jurisdiction: str,
        *,
        domains: Sequence[str] | None = None,
        task: str = "",
        agent: str = "general",
        retrieval_query: str | None = None,
        emit: EventSink | None = None,
    ) -> SpecialistResult:
        emit = emit or _no_events
        emit("status", {"stage": "retrieving", "jurisdiction": jurisdiction})
        retrieved = self.retriever.search(retrieval_query or question, jurisdiction, domains)
        return self.answer_from(retrieved, question, jurisdiction, task=task, agent=agent, emit=emit)

    def answer_from(
        self,
        retrieved: list[RetrievedChunk],
        question: str,
        jurisdiction: str,
        *,
        task: str = "",
        agent: str = "general",
        emit: EventSink | None = None,
    ) -> SpecialistResult:
        """Write and check an answer from already-retrieved chunks."""
        emit = emit or _no_events
        if not retrieved:
            reason = "no_corpus" if self.retriever.repository.active_chunk_count(jurisdiction) == 0 else "no_sources"
            return self.abstain(jurisdiction, reason, agent, retrieved)

        if self.llm is None:
            return self.extractive(jurisdiction, retrieved, agent)
        emit("status", {"stage": "writing", "jurisdiction": jurisdiction})
        try:
            draft = self.llm.complete(GROUNDED_SYSTEM, grounded_user_prompt(question, jurisdiction, retrieved, task))
        except LLMError as exc:
            log.warning("LLM unavailable, using extractive answer: %s", exc)
            return self.extractive(jurisdiction, retrieved, agent)
        emit("status", {"stage": "verifying", "jurisdiction": jurisdiction})
        return self.finalize(draft, jurisdiction, retrieved, agent, question)

    def finalize(
        self, draft: str, jurisdiction: str, retrieved: list[RetrievedChunk], agent: str, question: str = ""
    ) -> SpecialistResult:
        """Citation check → verification → confidence → answer or abstention."""
        if INSUFFICIENT in draft:
            return self.abstain(jurisdiction, "insufficient_evidence", agent, retrieved, related=True)
        markdown, cited = renumber_citations(draft, retrieved)
        if not cited:
            return self.abstain(jurisdiction, "no_citations", agent, retrieved, related=True)

        supported: float | None = None
        if self.verify and self.llm is not None:
            try:
                check = verify_answer(self.llm, markdown, cited, question)
            except LLMError as exc:
                log.warning("Citation verification unavailable: %s", exc)
            else:
                if not check.on_point:  # accurate about the sources, but the sources are about something else
                    return self.abstain(jurisdiction, "not_on_point", agent, retrieved, related=True)
                supported = check.supported_fraction
                markdown, cited = renumber_citations(check.markdown, cited)
                if supported < MIN_SUPPORTED_FRACTION or not cited:
                    return self.abstain(
                        jurisdiction, "unsupported", agent, retrieved, related=True, signals={"verification": supported}
                    )

        confidence, signals = conf.score(cited, retrieved, supported)
        if confidence < self.threshold:
            return self.abstain(
                jurisdiction, "low_confidence", agent, retrieved, confidence, related=True, signals=signals.as_dict()
            )
        return SpecialistResult(
            jurisdiction=jurisdiction,
            answer_markdown=markdown,
            citations=cited,
            confidence=confidence,
            abstained=False,
            agent=agent,
            retrieved=retrieved,
            signals=signals.as_dict(),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def abstain(
        jurisdiction: str,
        reason: str,
        agent: str,
        retrieved: list[RetrievedChunk],
        confidence: float = 0.0,
        *,
        related: bool = False,
        signals: dict[str, float] | None = None,
    ) -> SpecialistResult:
        """A withheld answer. With `related`, the top sources are offered as pointers (not as an answer)."""
        return SpecialistResult(
            jurisdiction=jurisdiction,
            answer_markdown="",
            citations=retrieved[:RELATED_LIMIT] if related else [],
            confidence=confidence,
            abstained=True,
            abstain_reason=reason,
            mode="abstained",
            agent=agent,
            retrieved=retrieved,
            signals=signals or {},
        )

    def extractive(self, jurisdiction: str, retrieved: list[RetrievedChunk], agent: str, limit: int = 3) -> SpecialistResult:
        """No LLM: quote the top provisions verbatim, still gated by retrieval confidence."""
        # Quote only clearly relevant provisions (always at least the best one)
        cutoff = max(0.25, retrieved[0].relevance * 0.5)
        top = [retrieved[0]] + [r for r in retrieved[1:limit] if r.relevance >= cutoff]
        confidence, signals = conf.score(top[:1], retrieved, None)
        if confidence < self.threshold:
            return self.abstain(
                jurisdiction, "low_confidence", agent, retrieved, confidence, related=True, signals=signals.as_dict()
            )
        lines = [msg("extractive_intro"), ""]
        for index, item in enumerate(top, start=1):
            c = item.chunk
            lines.append(f"- **{c.title} — {c.section_ref}:** “{_snippet(c.text)}” [S{index}]")
        return SpecialistResult(
            jurisdiction=jurisdiction,
            answer_markdown="\n".join(lines),
            citations=top,
            confidence=confidence,
            abstained=False,
            mode="extractive",
            agent=agent,
            retrieved=retrieved,
            signals=signals.as_dict(),
        )

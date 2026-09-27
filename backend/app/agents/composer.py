"""Composer: turns specialist results into the API's per-jurisdiction answer blocks."""

from __future__ import annotations

from app.agents.types import SpecialistResult
from app.guardrails.messages import msg
from app.retrieval.search import RetrievedChunk
from app.schemas import AnswerBlock, Citation

ABSTAIN_MESSAGE_KEYS = {
    "no_corpus": "abstain_no_corpus",
    "no_sources": "abstain_no_sources",
    "insufficient_evidence": "abstain_insufficient",
    "no_citations": "abstain_insufficient",
    "unsupported": "abstain_insufficient",
    "low_confidence": "abstain_low_confidence",
}


def confidence_label(confidence: float, threshold: float) -> str:
    """High / Medium / Low badge. Anything under the abstention threshold is Low."""
    if confidence >= max(0.75, threshold):
        return "high"
    if confidence >= threshold:
        return "medium"
    return "low"


def to_citation(marker: int, item: RetrievedChunk, snippet_chars: int = 2000) -> Citation:
    c = item.chunk
    text = c.text.strip()
    return Citation(
        marker=marker,
        chunk_id=c.chunk_id,
        doc_id=c.doc_id,
        doc_title=c.title,
        section_ref=c.section_ref,
        jurisdiction=c.jurisdiction,
        version_date=c.version_date,
        version=c.version,
        source_url=c.source_url,
        file=c.file,
        page=c.page,
        snippet=text if len(text) <= snippet_chars else text[:snippet_chars] + " …",
    )


def to_block(result: SpecialistResult, threshold: float, language: str = "en") -> AnswerBlock:
    if result.abstained:
        markdown = msg(ABSTAIN_MESSAGE_KEYS.get(result.abstain_reason or "", "abstain_insufficient"), language)
        return AnswerBlock(
            jurisdiction=result.jurisdiction,
            markdown=markdown,
            citations=[],
            confidence=round(result.confidence, 3),
            confidence_label="low",
            abstained=True,
            abstain_reason=result.abstain_reason,
            mode="abstained",
        )
    return AnswerBlock(
        jurisdiction=result.jurisdiction,
        markdown=result.answer_markdown,
        citations=[to_citation(i, item) for i, item in enumerate(result.citations, start=1)],
        confidence=round(result.confidence, 3),
        confidence_label=confidence_label(result.confidence, threshold),
        abstained=False,
        mode=result.mode,
    )

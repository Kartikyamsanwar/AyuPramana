"""Composer: merges specialist results into ONE cited answer block per jurisdiction.

When two specialists answer (e.g. IP + ABS), their parts get sub-headings and their
citation markers are renumbered into a single list. India and International results
are composed separately and never mixed.
"""

from __future__ import annotations

from app.agents.citations import shift_markers
from app.agents.types import SpecialistResult
from app.guardrails.messages import msg
from app.retrieval.search import RetrievedChunk
from app.schemas import AnswerBlock, Citation

ABSTAIN_MESSAGE_KEYS = {
    "no_corpus": "abstain_no_corpus",
    "no_sources": "abstain_no_sources",
    "insufficient_evidence": "abstain_insufficient",
    "no_citations": "abstain_insufficient",
    "not_on_point": "abstain_insufficient",
    "unsupported": "abstain_unsupported",
    "low_confidence": "abstain_low_confidence",
    "out_of_scope_medical": "out_of_scope_medical",
    "off_topic": "off_topic",
}


def confidence_label(confidence: float, threshold: float) -> str:
    """High / Medium / Low badge. Anything under the abstention threshold is Low."""
    if confidence >= max(0.75, threshold):
        return "high"
    if confidence >= threshold:
        return "medium"
    return "low"


def agent_title(agent: str, language: str) -> str:
    key = f"agent_{agent}"
    try:
        return msg(key, language)
    except KeyError:
        return agent.replace("_", " ").title()


def merge_results(results: list[SpecialistResult], language: str = "en") -> SpecialistResult:
    """Combine several specialists' results for one jurisdiction."""
    if len(results) == 1:
        return results[0]
    answered = [r for r in results if not r.abstained]
    if not answered:
        return results[0]

    citations: list[RetrievedChunk] = []
    position: dict[str, int] = {}
    parts: list[str] = []
    for result in answered:
        mapping: dict[int, int] = {}
        for local, item in enumerate(result.citations, start=1):
            key = item.chunk.chunk_id
            if key not in position:
                citations.append(item)
                position[key] = len(citations)
            mapping[local] = position[key]
        body = shift_markers(result.answer_markdown, mapping)
        section = f"### {agent_title(result.agent, language)}\n\n{body}"
        if result.appendix:
            section += f"\n\n{result.appendix}"
        parts.append(section)

    skipped = [r for r in results if r.abstained]
    if skipped:
        topics = ", ".join(agent_title(r.agent, language).lower() for r in skipped)
        parts.append("_" + msg("partial_answer", language).format(topics=topics) + "_")

    weakest = min(answered, key=lambda r: r.confidence)
    return SpecialistResult(
        jurisdiction=answered[0].jurisdiction,
        answer_markdown="\n\n".join(parts),
        citations=citations,
        confidence=weakest.confidence,  # a combined answer is only as strong as its weakest part
        abstained=False,
        mode="extractive" if any(r.mode == "extractive" for r in answered) else "generated",
        agent="+".join(r.agent for r in results),
        retrieved=[c for r in results for c in r.retrieved],
        signals=weakest.signals,
    )


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
    citations = [to_citation(i, item) for i, item in enumerate(result.citations, start=1)]
    appendix = f"\n\n{result.appendix}" if result.appendix else ""
    if result.abstained:
        markdown = msg(ABSTAIN_MESSAGE_KEYS.get(result.abstain_reason or "", "abstain_insufficient"), language)
        if citations:
            # Pointers only — clearly labelled, not presented as an answer
            related = "\n".join(f"- {c.doc_title} — {c.section_ref} [S{c.marker}]" for c in citations)
            markdown += f"\n\n{msg('possibly_related', language)}\n\n{related}"
        return AnswerBlock(
            jurisdiction=result.jurisdiction,
            markdown=markdown + appendix,
            citations=citations,
            confidence=round(result.confidence, 3),
            confidence_label="low",
            abstained=True,
            abstain_reason=result.abstain_reason,
            mode="abstained",
            escalation_suggested=result.abstain_reason not in ("out_of_scope_medical", "off_topic"),
            signals=result.signals,
        )
    label = confidence_label(result.confidence, threshold)
    return AnswerBlock(
        jurisdiction=result.jurisdiction,
        markdown=result.answer_markdown + appendix,
        citations=citations,
        confidence=round(result.confidence, 3),
        confidence_label=label,
        abstained=False,
        mode=result.mode,
        escalation_suggested=label == "low",
        signals=result.signals,
    )

"""Confidence score (0-1) for an answer, built from three explainable signals.

1. retrieval    — how relevant the best cited source is (reranker probability, or
                  calibrated cosine similarity when the reranker is off)
2. agreement    — share of the top-3 sources that BOTH keyword and vector search found
                  (two independent methods agreeing is a good sign)
3. verification — share of the answer's statements the LLM fact-check found supported
                  by the cited sources

confidence = 0.45 x retrieval + 0.15 x agreement + 0.40 x verification

Without a verification result (LLM down, or check disabled) the first two signals are
re-weighted, and the score is capped just below "High": unverified answers are never High.
Answers under CONFIDENCE_THRESHOLD are withheld (abstention) and escalation is offered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.retrieval.search import RetrievedChunk

W_RETRIEVAL, W_AGREEMENT, W_VERIFICATION = 0.45, 0.15, 0.40
UNVERIFIED_CAP = 0.74


@dataclass(frozen=True)
class ConfidenceSignals:
    retrieval: float
    agreement: float
    verification: float | None

    def as_dict(self) -> dict[str, float]:
        data = {"retrieval": round(self.retrieval, 3), "agreement": round(self.agreement, 3)}
        if self.verification is not None:
            data["verification"] = round(self.verification, 3)
        return data


def retrieval_signal(cited: Sequence[RetrievedChunk], retrieved: Sequence[RetrievedChunk]) -> float:
    pool = cited or retrieved[:1]
    return max((c.relevance for c in pool), default=0.0)


def agreement_signal(retrieved: Sequence[RetrievedChunk], n: int = 3) -> float:
    top = list(retrieved[:n])
    if not top:
        return 0.0
    return sum(1 for r in top if r.in_vector and r.in_bm25) / len(top)


def combine(signals: ConfidenceSignals) -> float:
    if signals.verification is None:
        score = (W_RETRIEVAL * signals.retrieval + W_AGREEMENT * signals.agreement) / (W_RETRIEVAL + W_AGREEMENT)
        return round(min(score, UNVERIFIED_CAP), 3)
    score = (
        W_RETRIEVAL * signals.retrieval + W_AGREEMENT * signals.agreement + W_VERIFICATION * signals.verification
    )
    return round(max(0.0, min(1.0, score)), 3)


def score(
    cited: Sequence[RetrievedChunk], retrieved: Sequence[RetrievedChunk], verification: float | None
) -> tuple[float, ConfidenceSignals]:
    signals = ConfidenceSignals(retrieval_signal(cited, retrieved), agreement_signal(retrieved), verification)
    return combine(signals), signals

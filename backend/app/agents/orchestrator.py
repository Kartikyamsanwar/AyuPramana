"""Orchestrator: handles one chat turn end to end.

scrub PII → answer separately for each jurisdiction → compose blocks → audit log.
"""

from __future__ import annotations

import time

from app.agents.composer import to_block
from app.agents.grounded import GroundedAnswerer
from app.config import Settings
from app.db.audit import AuditLog
from app.guardrails.messages import msg
from app.guardrails.pii import scrub
from app.schemas import AnswerBlock, ChatRequest, ChatResponse


def jurisdictions_for(choice: str) -> list[str]:
    """'both' means two independent answers — India and International are never mixed."""
    return ["india", "international"] if choice == "both" else [choice]


class ChatService:
    def __init__(self, settings: Settings, answerer: GroundedAnswerer, audit: AuditLog) -> None:
        self.settings = settings
        self.answerer = answerer
        self.audit = audit

    def handle(self, request: ChatRequest, source: str = "chat") -> ChatResponse:
        started = time.perf_counter()
        question = scrub(request.message).text

        blocks: dict[str, AnswerBlock] = {}
        for jurisdiction in jurisdictions_for(request.jurisdiction):
            result = self.answerer.answer(question, jurisdiction)
            blocks[jurisdiction] = to_block(result, self.settings.confidence_threshold, request.language)

        query_id = self.audit.record_query(
            session_id=request.session_id,
            language=request.language,
            jurisdiction=request.jurisdiction,
            scrubbed_query=question,
            intents=["general"],
            blocks=blocks,
            latency_ms=int((time.perf_counter() - started) * 1000),
            llm_provider=self.settings.llm_provider if self.answerer.llm else "none",
            source=source,
        )
        return ChatResponse(
            query_id=query_id,
            answers=blocks,
            disclaimer=msg("disclaimer", request.language),
            language=request.language,
        )

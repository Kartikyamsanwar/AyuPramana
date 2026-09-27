"""Audit log writes. Callers must pass already PII-scrubbed text."""

from __future__ import annotations

import json

from app.db.models import QueryLog
from app.db.session import SessionFactory
from app.schemas import AnswerBlock


class AuditLog:
    def __init__(self, session_factory: SessionFactory, enabled: bool = True) -> None:
        self._session_factory = session_factory
        self.enabled = enabled

    def record_query(
        self,
        *,
        session_id: str,
        language: str,
        jurisdiction: str,
        scrubbed_query: str,
        intents: list[str],
        blocks: dict[str, AnswerBlock],
        latency_ms: int,
        llm_provider: str,
        source: str = "chat",
    ) -> int | None:
        if not self.enabled:
            return None
        summary = {
            key: {
                "confidence": block.confidence,
                "abstained": block.abstained,
                "reason": block.abstain_reason,
                "mode": block.mode,
                "citations": [f"{c.doc_id} {c.section_ref}" for c in block.citations],
            }
            for key, block in blocks.items()
        }
        confidences = [b.confidence for b in blocks.values()]
        row = QueryLog(
            session_id=session_id,
            language=language,
            jurisdiction=jurisdiction,
            query_text=scrubbed_query,
            intents=json.dumps(intents),
            blocks_summary=json.dumps(summary, ensure_ascii=False),
            min_confidence=min(confidences) if confidences else None,
            abstained=any(b.abstained for b in blocks.values()),
            latency_ms=latency_ms,
            llm_provider=llm_provider,
            source=source,
        )
        with self._session_factory() as session:
            session.add(row)
            session.commit()
            return row.id

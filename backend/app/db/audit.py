"""Audit log writes. Callers must pass already PII-scrubbed text."""

from __future__ import annotations

import json

from sqlalchemy import func, select

from app.db.models import Escalation, Feedback, QueryLog
from app.db.session import SessionFactory
from app.schemas import (
    AdminEscalation,
    AdminFeedback,
    AdminOverview,
    AdminQuery,
    AdminStats,
    AnswerBlock,
)


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

    def record_escalation(
        self, *, session_id: str, query_id: int | None, jurisdiction: str | None, language: str, scrubbed_note: str
    ) -> int:
        """Always recorded (even with LOG_QUERIES=false): the user explicitly asked for a human."""
        row = Escalation(
            session_id=session_id,
            query_id=query_id,
            jurisdiction=jurisdiction,
            language=language,
            note=scrubbed_note,
        )
        with self._session_factory() as session:
            if query_id is not None and session.get(QueryLog, query_id) is None:
                row.query_id = None  # unknown or unlogged query
            session.add(row)
            session.commit()
            return row.id

    def record_feedback(
        self, *, session_id: str, query_id: int | None, jurisdiction: str | None, rating: str, scrubbed_comment: str
    ) -> int:
        row = Feedback(
            session_id=session_id, query_id=query_id, jurisdiction=jurisdiction, rating=rating, comment=scrubbed_comment
        )
        with self._session_factory() as session:
            if query_id is not None and session.get(QueryLog, query_id) is None:
                row.query_id = None
            session.add(row)
            session.commit()
            return row.id

    def overview(self, limit: int = 50, include_eval: bool = False) -> AdminOverview:
        """Numbers and recent rows for the Audit page. Only scrubbed text is ever stored, so nothing extra to hide."""
        with self._session_factory() as session:
            query_filter = [] if include_eval else [QueryLog.source == "chat"]
            total = session.scalar(select(func.count()).select_from(QueryLog).where(*query_filter)) or 0
            abstained = session.scalar(
                select(func.count()).select_from(QueryLog).where(*query_filter, QueryLog.abstained.is_(True))
            ) or 0
            avg_conf = session.scalar(
                select(func.avg(QueryLog.min_confidence)).where(*query_filter, QueryLog.abstained.is_(False))
            )
            by_language = dict(
                session.execute(
                    select(QueryLog.language, func.count()).where(*query_filter).group_by(QueryLog.language)
                ).all()
            )
            ups = session.scalar(select(func.count()).select_from(Feedback).where(Feedback.rating == "up")) or 0
            downs = session.scalar(select(func.count()).select_from(Feedback).where(Feedback.rating == "down")) or 0
            escalation_count = session.scalar(select(func.count()).select_from(Escalation)) or 0

            queries = session.scalars(
                select(QueryLog).where(*query_filter).order_by(QueryLog.id.desc()).limit(limit)
            ).all()
            feedback = session.scalars(select(Feedback).order_by(Feedback.id.desc()).limit(limit)).all()
            escalations = session.scalars(select(Escalation).order_by(Escalation.id.desc()).limit(limit)).all()

        return AdminOverview(
            stats=AdminStats(
                queries=total,
                abstention_rate=round(abstained / total, 3) if total else None,
                avg_confidence=round(avg_conf, 3) if avg_conf is not None else None,
                feedback_up=ups,
                feedback_down=downs,
                escalations=escalation_count,
                by_language=by_language,
            ),
            queries=[
                AdminQuery(
                    id=q.id,
                    created_at=q.created_at.isoformat(timespec="seconds"),
                    language=q.language,
                    jurisdiction=q.jurisdiction,
                    query_text=q.query_text,
                    intents=json.loads(q.intents or "[]"),
                    blocks=json.loads(q.blocks_summary or "{}"),
                    min_confidence=q.min_confidence,
                    abstained=q.abstained,
                    latency_ms=q.latency_ms,
                    llm_provider=q.llm_provider,
                    source=q.source,
                )
                for q in queries
            ],
            feedback=[
                AdminFeedback(
                    id=f.id,
                    query_id=f.query_id,
                    jurisdiction=f.jurisdiction,
                    rating=f.rating,
                    comment=f.comment,
                    created_at=f.created_at.isoformat(timespec="seconds"),
                )
                for f in feedback
            ],
            escalations=[
                AdminEscalation(
                    id=e.id,
                    reference=f"ESC-{e.id:05d}",
                    query_id=e.query_id,
                    jurisdiction=e.jurisdiction,
                    language=e.language,
                    note=e.note,
                    status=e.status,
                    created_at=e.created_at.isoformat(timespec="seconds"),
                )
                for e in escalations
            ],
        )

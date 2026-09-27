"""Orchestrator: runs one chat turn end to end.

    PII scrub
      → pending clarifying question?  (formulation classifier flow)
      → Router agent: scope + intents
      → out of scope?  → polite abstention
      → specialists, separately for each jurisdiction (in parallel)
      → Composer: one cited block per jurisdiction
      → audit log (PII-scrubbed)
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from app.agents.base import EventSink, TurnContext
from app.agents.composer import merge_results, to_block
from app.agents.formulation import FLOW, FormulationClassifierAgent
from app.agents.grounded import GroundedAnswerer
from app.agents.registry import RegistryNavigatorAgent
from app.agents.router import Route, Router
from app.agents.session_state import FlowState, SessionStore
from app.agents.types import SpecialistResult
from app.config import Settings
from app.db.audit import AuditLog
from app.guardrails.messages import msg
from app.guardrails.pii import scrub
from app.schemas import AnswerBlock, ChatRequest, ChatResponse, QuickReply

STARTERS = ("starter_patent", "starter_plant", "starter_classify")


def jurisdictions_for(choice: str) -> list[str]:
    """'both' means two independent answers — India and International are never mixed."""
    return ["india", "international"] if choice == "both" else [choice]


def _no_events(event: str, data: dict) -> None:
    return None


@dataclass
class TurnTrace:
    """Internal details of a turn, used by the evaluation script (not sent to the browser)."""

    question_en: str = ""
    route: Route | None = None
    results: dict[str, SpecialistResult] = field(default_factory=dict)


class ChatService:
    def __init__(
        self,
        settings: Settings,
        answerer: GroundedAnswerer,
        audit: AuditLog,
        router: Router,
        specialists: dict,
        formulation: FormulationClassifierAgent,
        sessions: SessionStore,
    ) -> None:
        self.settings = settings
        self.answerer = answerer
        self.audit = audit
        self.router = router
        self.specialists = specialists
        self.formulation = formulation
        self.sessions = sessions

    def handle(self, request: ChatRequest, source: str = "chat", emit: EventSink | None = None) -> ChatResponse:
        return self.handle_with_trace(request, source, emit)[0]

    def handle_with_trace(
        self, request: ChatRequest, source: str = "chat", emit: EventSink | None = None
    ) -> tuple[ChatResponse, TurnTrace]:
        emit = emit or _no_events
        started = time.perf_counter()
        language = request.language
        question = scrub(request.message).text
        trace = TurnTrace(question_en=question)
        jurisdictions = jurisdictions_for(request.jurisdiction)

        def finish(
            results: dict[str, SpecialistResult] | None = None,
            intents: list[str] | None = None,
            follow_up: str | None = None,
            quick_replies: list[QuickReply] | None = None,
            notice: str | None = None,
        ) -> tuple[ChatResponse, TurnTrace]:
            results = results or {}
            trace.results = results
            blocks: dict[str, AnswerBlock] = {}
            for jurisdiction, result in results.items():
                block = to_block(result, self.settings.confidence_threshold, language)
                if notice:
                    block.escalation_suggested = True
                blocks[jurisdiction] = block
                emit("block", block.model_dump())
            query_id = self.audit.record_query(
                session_id=request.session_id,
                language=language,
                jurisdiction=request.jurisdiction,
                scrubbed_query=question,
                intents=intents or [],
                blocks=blocks,
                latency_ms=int((time.perf_counter() - started) * 1000),
                llm_provider=self.settings.llm_provider if self.answerer.llm else "none",
                source=source,
            )
            response = ChatResponse(
                query_id=query_id,
                answers=blocks,
                follow_up_question=follow_up,
                quick_replies=quick_replies or [],
                notice=notice,
                intents=intents or [],
                disclaimer=msg("disclaimer", language),
                language=language,
            )
            return response, trace

        # 1. Is this an answer to a pending clarifying question?
        state = self.sessions.get(request.session_id)
        if state is not None and state.flow == FLOW:
            choice = self.formulation.match_reply(state, request.message, request.quick_reply_id, language)
            if choice == "cancel":
                self.sessions.clear(request.session_id)
                return finish(intents=["formulation_classification"], follow_up=msg("flow_cancelled", language))
            if choice is not None:
                prompt = self.formulation.advance(request.session_id, state, choice, language)
                if prompt is not None:
                    return finish(
                        intents=["formulation_classification"],
                        follow_up=prompt.question,
                        quick_replies=prompt.quick_replies,
                    )
                self.sessions.clear(request.session_id)
                return finish(self._classify(state, request, jurisdictions, emit), ["formulation_classification"])
            self.sessions.clear(request.session_id)  # the user moved on to a new question

        # 2. Route
        emit("status", {"stage": "routing"})
        route = self.router.route(question)
        trace.route = route

        if route.scope == "greeting":
            starters = [QuickReply(id=f"starter:{key}", label=msg(key, language)) for key in STARTERS]
            return finish(follow_up=msg("greeting", language), quick_replies=starters)
        if route.scope in ("medical_advice", "off_topic"):
            reason = "out_of_scope_medical" if route.scope == "medical_advice" else "off_topic"
            results = {j: self.answerer.abstain(j, reason, "router", []) for j in jurisdictions}
            return finish(results, [route.scope])

        intents = list(route.intents)
        if intents and intents[0] == "formulation_classification":
            prompt = self.formulation.start(request.session_id, question, language)
            if prompt is not None:
                return finish(
                    intents=intents,
                    follow_up=f"{msg('flow_intro', language)}\n\n{prompt.question}",
                    quick_replies=prompt.quick_replies,
                )

        # 3. Specialists, per jurisdiction
        ctx = TurnContext(question, route.search_query or question, language, request.session_id, emit)

        def run_for(jurisdiction: str) -> SpecialistResult:
            results = [self._run_specialist(intent, ctx, jurisdiction, intents) for intent in intents]
            return merge_results(results, language)

        notice = msg("legal_advice_notice", language) if route.scope == "personal_legal_advice" else None
        return finish(self._parallel(jurisdictions, run_for), intents, notice=notice)

    # ------------------------------------------------------------------
    def _run_specialist(self, intent: str, ctx: TurnContext, jurisdiction: str, intents: list[str]) -> SpecialistResult:
        agent = self.specialists.get(intent) or self.specialists["general_regulatory"]
        if isinstance(agent, RegistryNavigatorAgent):
            return agent.run(ctx, jurisdiction, intents)
        return agent.run(ctx, jurisdiction)

    def _classify(
        self, state: FlowState, request: ChatRequest, jurisdictions: list[str], emit: EventSink
    ) -> dict[str, SpecialistResult]:
        ctx = TurnContext(state.original_question, state.original_question, request.language, request.session_id, emit)
        return self._parallel(jurisdictions, lambda j: self.formulation.classify(ctx, j, state))

    @staticmethod
    def _parallel(
        jurisdictions: list[str], work: Callable[[str], SpecialistResult]
    ) -> dict[str, SpecialistResult]:
        """India and International are answered independently, at the same time."""
        if len(jurisdictions) == 1:
            return {jurisdictions[0]: work(jurisdictions[0])}
        with ThreadPoolExecutor(max_workers=len(jurisdictions)) as pool:
            futures = {j: pool.submit(work, j) for j in jurisdictions}
            return {j: future.result() for j, future in futures.items()}

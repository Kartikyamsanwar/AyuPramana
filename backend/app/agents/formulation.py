"""Formulation Classifier agent.

A short clarifying flow (max ~4 questions, one at a time, as quick-reply buttons) collects
facts about the product. The agent then retrieves the category definitions and the
IP / ABS / advertising provisions from the corpus, and the LLM places the product in a
category using ONLY those retrieved definitions, with citations. The questions live in
data/formulation_flow.yaml so the team can edit and verify them without touching code.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from app.agents.base import TurnContext
from app.agents.grounded import GroundedAnswerer
from app.agents.session_state import FlowState, SessionStore
from app.agents.types import SpecialistResult
from app.retrieval.search import RetrievedChunk
from app.schemas import QuickReply

log = logging.getLogger(__name__)

FLOW = "formulation"
CANCEL_ID = "flow:cancel"
CANCEL_WORDS = {"cancel", "stop", "exit", "रद्द करें", "रद्द करा"}
MAX_SOURCES = 10


class Localized(BaseModel):
    en: str
    hi: str | None = None
    mr: str | None = None

    def get(self, language: str) -> str:
        return getattr(self, language, None) or self.en


class Option(BaseModel):
    id: str
    label: Localized


class Question(BaseModel):
    id: str
    text: Localized
    options: list[Option]


class Category(BaseModel):
    id: str
    label: Localized
    search: str
    domains: list[str] = []


class PostureSearch(BaseModel):
    search: str
    domains: list[str] = []


class FlowConfig(BaseModel):
    verified: bool = False
    max_questions: int = 4
    questions: list[Question]
    categories: list[Category]
    posture_searches: list[PostureSearch] = []


def load_flow(path: Path) -> FlowConfig | None:
    try:
        return FlowConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        log.error("formulation_flow.yaml could not be loaded: %s", exc)
        return None


class FlowPrompt(BaseModel):
    question: str
    quick_replies: list[QuickReply]


CLASSIFY_TASK_INDIA = """PRODUCT FACTS (the user's answers):
{facts}

CANDIDATE CATEGORIES: {categories}

Using only the SOURCES:
1. Say which ONE candidate category best fits this product, based on the legal definitions in the SOURCES, and why. If the SOURCES do not define the categories clearly enough to decide, say the category cannot be determined from the available sources.
2. Summarise what that category requires (licences, approvals, conditions) according to the SOURCES.
3. Note the intellectual-property, access-and-benefit-sharing and advertising points the SOURCES raise for such a product.
Begin with a line of the form: **Likely category:** <category name>"""

CLASSIFY_TASK_INTERNATIONAL = """PRODUCT FACTS (the user's answers):
{facts}

Product categories are defined by national law. Using only the SOURCES, explain the international intellectual-property and access-and-benefit-sharing points relevant to a product like this."""


class FormulationClassifierAgent:
    name = "formulation_classification"

    def __init__(self, answerer: GroundedAnswerer, flow_path: Path, sessions: SessionStore) -> None:
        self.answerer = answerer
        self.flow_path = flow_path
        self.sessions = sessions

    # --- conversation -----------------------------------------------------
    def _config(self) -> FlowConfig | None:
        return load_flow(self.flow_path)

    def _questions(self, config: FlowConfig) -> list[Question]:
        return config.questions[: config.max_questions]

    def _prompt(self, config: FlowConfig, step: int, language: str) -> FlowPrompt:
        question = self._questions(config)[step]
        replies = [QuickReply(id=f"{question.id}:{o.id}", label=o.label.get(language)) for o in question.options]
        replies.append(QuickReply(id=CANCEL_ID, label={"hi": "रद्द करें", "mr": "रद्द करा"}.get(language, "Cancel")))
        total = len(self._questions(config))
        return FlowPrompt(question=f"({step + 1}/{total}) {question.text.get(language)}", quick_replies=replies)

    def start(self, session_id: str, original_question: str, language: str) -> FlowPrompt | None:
        config = self._config()
        if config is None or not config.questions:
            return None
        self.sessions.set(session_id, FlowState(flow=FLOW, original_question=original_question))
        return self._prompt(config, 0, language)

    def match_reply(self, state: FlowState, message: str, quick_reply_id: str | None, language: str) -> str | None:
        """Return the chosen option id, "cancel", or None if the message isn't an answer to the current question."""
        config = self._config()
        if config is None:
            return None
        if quick_reply_id == CANCEL_ID or message.strip().lower() in CANCEL_WORDS:
            return "cancel"
        question = self._questions(config)[state.step]
        for option in question.options:
            if quick_reply_id == f"{question.id}:{option.id}":
                return option.id
            labels = {option.label.en, *(v for v in (option.label.hi, option.label.mr) if v)}
            if message.strip().casefold() in {label.casefold() for label in labels}:
                return option.id
        return None

    def advance(self, session_id: str, state: FlowState, option_id: str, language: str) -> FlowPrompt | None:
        """Record an answer. Returns the next question, or None when the flow is complete."""
        config = self._config()
        questions = self._questions(config) if config else []
        if not questions:
            return None
        state.answers[questions[state.step].id] = option_id
        state.step += 1
        if state.step < len(questions):
            self.sessions.set(session_id, state)
            return self._prompt(config, state.step, language)  # type: ignore[arg-type]
        return None

    # --- classification -----------------------------------------------------
    def facts(self, answers: dict[str, str]) -> list[str]:
        config = self._config()
        if config is None:
            return []
        lines = []
        for question in self._questions(config):
            option = next((o for o in question.options if o.id == answers.get(question.id)), None)
            if option:
                lines.append(f"- {question.text.en} {option.label.en}")
        return lines

    def _retrieve(self, config: FlowConfig, jurisdiction: str) -> list[RetrievedChunk]:
        searches: list[tuple[str, list[str]]] = []
        if jurisdiction == "india":
            searches += [(c.search, c.domains) for c in config.categories]
        searches += [(p.search, p.domains) for p in config.posture_searches]
        seen: set[str] = set()
        results: list[RetrievedChunk] = []
        for query, domains in searches:
            for hit in self.answerer.retriever.search(query, jurisdiction, domains or None, top_k=2):
                if hit.chunk.chunk_id not in seen:
                    seen.add(hit.chunk.chunk_id)
                    results.append(hit)
        results.sort(key=lambda r: r.relevance, reverse=True)
        return results[:MAX_SOURCES]

    def classify(self, ctx: TurnContext, jurisdiction: str, state: FlowState) -> SpecialistResult:
        config = self._config()
        if config is None:
            return self.answerer.abstain(jurisdiction, "no_sources", self.name, [])
        ctx.emit("status", {"stage": "retrieving", "jurisdiction": jurisdiction})
        retrieved = self._retrieve(config, jurisdiction)
        facts = "\n".join(self.facts(state.answers)) or "- (no answers given)"
        if jurisdiction == "india":
            categories = "; ".join(c.label.en for c in config.categories)
            task = CLASSIFY_TASK_INDIA.format(facts=facts, categories=categories)
        else:
            task = CLASSIFY_TASK_INTERNATIONAL.format(facts=facts)
        question = state.original_question or "Which regulatory category does my Ayurvedic product fall into?"
        return self.answerer.answer_from(retrieved, question, jurisdiction, task=task, agent=self.name, emit=ctx.emit)

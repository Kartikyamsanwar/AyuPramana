"""Evaluation harness: runs the question set through the real pipeline and measures the four
things the judges score — retrieval/citation accuracy, safe abstention, confidence, and
per-language quality — plus latency.

Question file (data/eval/questions.jsonl), one JSON object per line:
    id, question, language (en|hi|mr), jurisdiction (india|international|both),
    expected_behavior (answer|abstain),
    expected_citations: [{"doc_id": "...", "section_ref": "Section 3", "jurisdiction": "india"}]  (jurisdiction optional)
    verified (true once a team member has checked the expectations against the real documents), notes
"""

from __future__ import annotations

import json
import re
import statistics
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from app.agents.orchestrator import ChatService
from app.schemas import ChatRequest


@dataclass
class EvalRow:
    id: str
    question: str
    language: str = "en"
    jurisdiction: str = "india"
    expected_behavior: str = "answer"
    expected_citations: list[dict] = field(default_factory=list)
    verified: bool = False
    notes: str = ""


@dataclass
class BlockOutcome:
    row_id: str
    jurisdiction: str
    language: str
    verified: bool
    expected_behavior: str
    outcome: str  # answered | abstained | clarify
    confidence: float | None
    retrieval_hit: bool | None  # None when no expected citations are recorded
    citation_precision: float | None
    citation_recall: float | None
    cited: list[str]
    latency_ms: int

    @property
    def abstention_correct(self) -> bool | None:
        if self.outcome == "clarify":
            return None
        return (self.outcome == "abstained") == (self.expected_behavior == "abstain")


def load_questions(path: Path) -> list[EvalRow]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} line {number}: {exc}") from exc
        rows.append(EvalRow(**{k: v for k, v in data.items() if k in EvalRow.__dataclass_fields__}))
    return rows


def _norm(section: str) -> str:
    return re.sub(r"\s+", " ", section.strip().lower())


def section_matches(expected: str, actual: str) -> bool:
    """'Section 3' matches 'Section 3', 'Section 3(k)–(p)' and 'Section 3 (part 2)', but not 'Section 30'."""
    e, a = _norm(expected), _norm(actual)
    return a == e or a.startswith(e + "(") or a.startswith(e + " ")


def _matches(expected: dict, doc_id: str, section_ref: str) -> bool:
    return expected.get("doc_id") == doc_id and section_matches(str(expected.get("section_ref", "")), section_ref)


def evaluate(
    chat: ChatService,
    rows: Iterable[EvalRow],
    pause: float = 0.0,
    progress: Callable[[str], None] = lambda _: None,
) -> list[BlockOutcome]:
    outcomes: list[BlockOutcome] = []
    for row in rows:
        request = ChatRequest(
            session_id=f"eval-{uuid.uuid4().hex[:16]}",  # fresh session: no flow state leaks between questions
            message=row.question,
            language=row.language,
            jurisdiction=row.jurisdiction,
        )
        started = time.perf_counter()
        response, trace = chat.handle_with_trace(request, source="eval")
        latency = int((time.perf_counter() - started) * 1000)

        if not response.answers:  # a clarifying question (formulation flow) or a greeting
            for jurisdiction in (["india", "international"] if row.jurisdiction == "both" else [row.jurisdiction]):
                outcomes.append(
                    BlockOutcome(row.id, jurisdiction, row.language, row.verified, row.expected_behavior,
                                 "clarify", None, None, None, None, [], latency)
                )
        for jurisdiction, block in response.answers.items():
            expected = [c for c in row.expected_citations if c.get("jurisdiction", jurisdiction) == jurisdiction]
            result = trace.results.get(jurisdiction)
            retrieved = result.retrieved if result else []
            hit = (
                any(_matches(e, r.chunk.doc_id, r.chunk.section_ref) for e in expected for r in retrieved)
                if expected
                else None
            )
            precision = recall = None
            if expected and not block.abstained:
                good = [c for c in block.citations if any(_matches(e, c.doc_id, c.section_ref) for e in expected)]
                precision = len(good) / len(block.citations) if block.citations else 0.0
                recall = sum(
                    1 for e in expected if any(_matches(e, c.doc_id, c.section_ref) for c in block.citations)
                ) / len(expected)
            outcomes.append(
                BlockOutcome(
                    row_id=row.id,
                    jurisdiction=jurisdiction,
                    language=row.language,
                    verified=row.verified,
                    expected_behavior=row.expected_behavior,
                    outcome="abstained" if block.abstained else "answered",
                    confidence=block.confidence,
                    retrieval_hit=hit,
                    citation_precision=precision,
                    citation_recall=recall,
                    cited=[f"{c.doc_id} {c.section_ref}" for c in block.citations if not block.abstained],
                    latency_ms=latency,
                )
            )
        progress(f"{row.id}: " + ", ".join(f"{o.jurisdiction}={o.outcome}" for o in outcomes if o.row_id == row.id))
        if pause:
            time.sleep(pause)
    return outcomes


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def _rate(flags: list[bool]) -> float | None:
    return round(sum(flags) / len(flags), 3) if flags else None


def summarize(outcomes: list[BlockOutcome]) -> dict:
    def block_stats(items: list[BlockOutcome]) -> dict:
        judged = [o.abstention_correct for o in items if o.abstention_correct is not None]
        return {
            "blocks": len(items),
            "abstention_accuracy": _rate(judged),
            "avg_confidence_answered": _mean([o.confidence for o in items if o.outcome == "answered" and o.confidence is not None]),
            "avg_latency_ms": _mean([o.latency_ms for o in items]),
        }

    latencies = sorted({(o.row_id, o.latency_ms) for o in outcomes}, key=lambda x: x[1])
    latency_values = [ms for _, ms in latencies]
    out_of_scope = [o for o in outcomes if o.expected_behavior == "abstain"]
    in_scope = [o for o in outcomes if o.expected_behavior == "answer" and o.outcome != "clarify"]
    return {
        "questions": len({o.row_id for o in outcomes}),
        "blocks": len(outcomes),
        "verified_blocks": sum(o.verified for o in outcomes),
        "retrieval_hit_rate": _rate([o.retrieval_hit for o in outcomes if o.retrieval_hit is not None]),
        "retrieval_judged": sum(o.retrieval_hit is not None for o in outcomes),
        "citation_precision": _mean([o.citation_precision for o in outcomes if o.citation_precision is not None]),
        "citation_recall": _mean([o.citation_recall for o in outcomes if o.citation_recall is not None]),
        "citation_judged": sum(o.citation_precision is not None for o in outcomes),
        "abstention_accuracy": _rate([o.abstention_correct for o in outcomes if o.abstention_correct is not None]),
        "out_of_scope_abstained": _rate([o.outcome == "abstained" for o in out_of_scope]),
        "in_scope_answered": _rate([o.outcome == "answered" for o in in_scope]),
        "avg_confidence_answered": _mean(
            [o.confidence for o in outcomes if o.outcome == "answered" and o.confidence is not None]
        ),
        "latency_p50_ms": int(statistics.median(latency_values)) if latency_values else None,
        "latency_p95_ms": int(latency_values[min(len(latency_values) - 1, int(0.95 * len(latency_values)))])
        if latency_values
        else None,
        "by_language": {
            lang: block_stats([o for o in outcomes if o.language == lang])
            for lang in sorted({o.language for o in outcomes})
        },
        "clarifications": sum(o.outcome == "clarify" for o in outcomes),
    }


def _fmt(value, percent: bool = False) -> str:
    if value is None:
        return "—"
    if percent:
        return f"{value * 100:.0f}%"
    return str(value)


def render_report(summary: dict, outcomes: list[BlockOutcome], meta: dict) -> str:
    lines = [
        "# AyuPramana — evaluation report",
        "",
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by `backend/scripts/eval.py`.",
        "",
        "| Setting | Value |",
        "|---|---|",
        *[f"| {key} | {value} |" for key, value in meta.items()],
        "",
        "## Summary",
        "",
        "| Metric | Value | What it means |",
        "|---|---|---|",
        f"| Questions / answer blocks | {summary['questions']} / {summary['blocks']} | 'Both' questions produce two blocks |",
        f"| Verified blocks | {summary['verified_blocks']} | Rows whose expectations a team member checked against the documents |",
        f"| Retrieval hit rate | {_fmt(summary['retrieval_hit_rate'], True)} (n={summary['retrieval_judged']}) | An expected provision was among the retrieved sources |",
        f"| Citation precision | {_fmt(summary['citation_precision'], True)} (n={summary['citation_judged']}) | Share of the answer's citations that are expected provisions |",
        f"| Citation recall | {_fmt(summary['citation_recall'], True)} (n={summary['citation_judged']}) | Share of expected provisions the answer cited |",
        f"| Abstention accuracy | {_fmt(summary['abstention_accuracy'], True)} | Answered when it should, abstained when it should |",
        f"| Out-of-scope abstained | {_fmt(summary['out_of_scope_abstained'], True)} | Safety: declined medical / unrelated questions |",
        f"| In-scope answered | {_fmt(summary['in_scope_answered'], True)} | Coverage: answered in-scope questions |",
        f"| Avg confidence (answered) | {_fmt(summary['avg_confidence_answered'])} | Mean confidence score of given answers |",
        f"| Latency p50 / p95 | {_fmt(summary['latency_p50_ms'])} ms / {_fmt(summary['latency_p95_ms'])} ms | Per question, end to end |",
        f"| Clarifying questions | {summary['clarifications']} | Blocks where the assistant asked a follow-up instead |",
        "",
        "## By language",
        "",
        "| Language | Blocks | Abstention accuracy | Avg confidence (answered) | Avg latency |",
        "|---|---|---|---|---|",
    ]
    for lang, stats in summary["by_language"].items():
        lines.append(
            f"| {lang} | {stats['blocks']} | {_fmt(stats['abstention_accuracy'], True)} | "
            f"{_fmt(stats['avg_confidence_answered'])} | {_fmt(stats['avg_latency_ms'])} ms |"
        )
    lines += [
        "",
        "## Per question",
        "",
        "| ID | Lang | Jurisdiction | Expected | Outcome | Confidence | Retrieval hit | Citation P / R | Cited | ms |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for o in outcomes:
        pr = "—" if o.citation_precision is None else f"{o.citation_precision:.2f} / {o.citation_recall:.2f}"
        hit = "—" if o.retrieval_hit is None else ("yes" if o.retrieval_hit else "no")
        flag = "" if o.verified else " *"
        cited = "; ".join(o.cited) or "—"
        lines.append(
            f"| {o.row_id}{flag} | {o.language} | {o.jurisdiction} | {o.expected_behavior} | {o.outcome} | "
            f"{_fmt(o.confidence)} | {hit} | {pr} | {cited} | {o.latency_ms} |"
        )
    lines += [
        "",
        "\\* not yet verified — expected citations have not been checked against the real documents, so retrieval and "
        "citation metrics for these rows are blank. Fill `expected_citations` in `data/eval/questions.jsonl` and set "
        "`verified: true`.",
        "",
    ]
    return "\n".join(lines)

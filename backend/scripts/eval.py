"""Run the evaluation set and write a Markdown report.

Usage (from the backend/ folder):
    python scripts/eval.py                        # all rows → ../docs/eval_report.md
    python scripts/eval.py --only-verified
    python scripts/eval.py --limit 5 --pause 3    # pause between questions (free-tier rate limits)

The report shows retrieval hit rate, citation precision/recall, abstention accuracy,
average confidence, per-language results and latency.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import REPO_ROOT, get_settings  # noqa: E402
from app.evaluation import evaluate, load_questions, render_report, summarize  # noqa: E402
from app.services import build_services  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", type=Path, default=None, help="default: data/eval/questions.jsonl")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "docs" / "eval_report.md")
    parser.add_argument("--only-verified", action="store_true", help="skip rows with verified=false")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pause", type=float, default=0.0, help="seconds to wait between questions")
    args = parser.parse_args()

    settings = get_settings()
    path = args.questions or settings.data_dir / "eval" / "questions.jsonl"
    rows = load_questions(path)
    if args.only_verified:
        rows = [r for r in rows if r.verified]
    rows = rows[: args.limit] if args.limit else rows
    if not rows:
        print(f"No questions to run in {path}.")
        return 1

    services = build_services(settings)
    documents, chunks = services.repository.corpus_counts()
    services.embedder.embed_query("warm-up")  # load the model first so it doesn't count as latency
    print(f"Running {len(rows)} questions against {documents} documents / {chunks} chunks …")
    outcomes = evaluate(services.chat, rows, pause=args.pause, progress=print)
    summary = summarize(outcomes)

    meta = {
        "LLM": f"{settings.llm_provider} / {settings.llm_model}" if services.llm else "none (extractive mode)",
        "Embedding model": services.embedder.model_name,
        "Reranker": settings.reranker_model if services.retriever.reranker else "off",
        "Citation verification": "on" if settings.citation_verification and services.llm else "off",
        "Translator": services.translator.name if services.translator else "none",
        "Confidence threshold": settings.confidence_threshold,
        "Corpus": f"{documents} documents, {chunks} chunks",
        "Question file": path.name,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(summary, outcomes, meta), encoding="utf-8")

    print("\nSummary")
    for key in ("retrieval_hit_rate", "citation_precision", "citation_recall", "abstention_accuracy",
                "out_of_scope_abstained", "in_scope_answered", "avg_confidence_answered",
                "latency_p50_ms", "latency_p95_ms"):
        print(f"  {key:26} {summary[key]}")
    print(f"\nReport written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

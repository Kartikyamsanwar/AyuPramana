"""Ingest the documents listed in data/manifest.yaml into SQLite + Chroma.

Usage (from the backend/ folder):
    python scripts/ingest.py --all
    python scripts/ingest.py --doc patents_act_1970
    python scripts/ingest.py --all --force      # rebuild even unchanged files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.ingest.manifest import ManifestError, load_manifest  # noqa: E402
from app.services import build_services  # noqa: E402

STATUS_ICONS = {
    "ingested": "NEW",
    "unchanged": "ok",
    "reembedded": "RE-EMBED",
    "missing_file": "MISSING",
    "no_text": "NO TEXT",
    "error": "ERROR",
    "unknown_id": "UNKNOWN",
}


def print_table(rows: list[list[str]], headers: list[str]) -> None:
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(x).ljust(w) for x, w in zip(row, widths)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="ingest every manifest entry")
    group.add_argument("--doc", action="append", metavar="ID", help="ingest one entry (repeatable)")
    parser.add_argument("--force", action="store_true", help="re-chunk and re-embed even if the file is unchanged")
    args = parser.parse_args()

    settings = get_settings()
    try:
        entries = load_manifest(settings.manifest_path)
    except ManifestError as exc:
        print(f"Manifest error: {exc}")
        return 2
    if not entries:
        print(f"No entries in {settings.manifest_path}. Add documents first (see docs/CORPUS_SOURCES.md).")
        return 0

    if settings.embedding_provider == "gemini":
        print(f"Embeddings: Gemini API ({settings.gemini_embedding_model}, {settings.gemini_embedding_dimensions} dims)")
    else:
        print(f"Embedding model: {settings.embedding_model}  (first run downloads it)")
    services = build_services(settings, llm=None)
    results = services.ingestor().ingest(doc_ids=args.doc, force=args.force)

    rows = [
        [STATUS_ICONS.get(r.status, r.status), r.doc_id, r.jurisdiction, r.chunks or "", r.version, r.message]
        for r in results
    ]
    print()
    print_table(rows, ["status", "id", "jurisdiction", "chunks", "version", "note"])
    missing = [r for r in results if r.status == "missing_file"]
    failed = [r for r in results if r.status in {"error", "no_text", "unknown_id"}]
    documents, chunks = services.repository.corpus_counts()
    print(f"\nCorpus: {documents} documents, {chunks} active chunks.")
    if missing:
        print(f"WARNING: {len(missing)} manifest entries have no file in data/raw/ yet.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

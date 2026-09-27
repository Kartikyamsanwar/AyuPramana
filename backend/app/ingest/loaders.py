"""Turn a PDF / HTML / text file into page-numbered plain text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".pdf", ".html", ".htm", ".txt", ".md"}


class UnsupportedFileError(ValueError):
    pass


@dataclass(frozen=True)
class PageText:
    page: int  # 1-based
    text: str


def _clean(text: str) -> str:
    """Normalise Unicode and whitespace but keep line breaks (the chunker relies on them)."""
    text = unicodedata.normalize("NFC", text).replace(" ", " ").replace("­", "")
    lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(lines)


def _load_pdf(path: Path) -> list[PageText]:
    import pymupdf

    with pymupdf.open(path) as pdf:
        return [PageText(page=i + 1, text=_clean(page.get_text("text"))) for i, page in enumerate(pdf)]


def _load_html(path: Path) -> list[PageText]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    return [PageText(page=1, text=_clean(soup.get_text("\n")))]


def _load_text(path: Path) -> list[PageText]:
    return [PageText(page=1, text=_clean(path.read_text(encoding="utf-8")))]


def load_document(path: Path) -> list[PageText]:
    """Extract text per page. Scanned PDFs without a text layer return pages with empty text."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix in {".html", ".htm"}:
        return _load_html(path)
    if suffix in {".txt", ".md"}:
        return _load_text(path)
    raise UnsupportedFileError(f"Unsupported file type '{suffix}' (use PDF, HTML or TXT)")

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


FOOTNOTE_MARK = "† "
_FOOTNOTE_SIZE_RATIO = 0.85


def _load_pdf(path: Path) -> list[PageText]:
    """Extract text line by line. Lines set in a clearly smaller font than the body text
    (footnotes such as "1. Subs. by Act 38 of 2002…") are prefixed with FOOTNOTE_MARK, so the
    chunker never mistakes them for section headings. Their text is kept."""
    import pymupdf

    with pymupdf.open(path) as pdf:
        # Content-stream order: measured better than position-sorted order on the official PDFs
        pages = [page.get_text("dict") for page in pdf]

    # Body font size = the size carrying the most characters in the document
    weight: dict[float, int] = {}
    for page in pages:
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = round(span.get("size", 0), 1)
                    weight[size] = weight.get(size, 0) + len(span.get("text", "").strip())
    body_size = max(weight, key=weight.get) if weight else 0

    result = []
    for number, page in enumerate(pages, start=1):
        lines = []
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in line["spans"])
                largest = max(s.get("size", 0) for s in spans)
                is_footnote = body_size and largest < body_size * _FOOTNOTE_SIZE_RATIO and len(text.strip()) > 3
                lines.append(FOOTNOTE_MARK + text.strip() if is_footnote else text)
            lines.append("")  # block boundary
        result.append(PageText(page=number, text=_clean("\n".join(lines))))
    return result


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

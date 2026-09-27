"""Section-aware chunking.

Legal texts are organised by headings: "Section 3", "3. What are not inventions.—",
"Article 5", "Rule 12", "THE FIRST SCHEDULE". We cut along those headings, so each
chunk belongs to exactly one provision. The heading is kept inside every chunk, and a
`section_ref` is recorded (e.g. "Section 3" or "Section 3(k)–(p)") for citations to show.
Provisions longer than the maximum are split into ~target-sized parts at clause
boundaries, with a small word overlap between consecutive parts.

Heuristics (all tested in tests/test_chunker.py):
* Cross-references in running text ("…under section 3, the…", "Article 5 of the…")
  are not headings: a heading must be followed by the end of the line or a Capitalised title.
* India Code footnotes ("1. Subs. by Act…") and numbers that go backwards are ignored.
* A table of contents ("ARRANGEMENT OF SECTIONS") becomes one "toc" chunk that is not
  used for answers; it ends when the numbering restarts at 1.
* Inside a Schedule, numbered items are part of the schedule, not new sections.
* PDFs often split "Article" and "15" onto two lines; they are joined first.
* A bare heading like "Article 15" only starts a provision if the previous line ended a
  sentence (otherwise it is a wrapped cross-reference: "...in accordance with / Article 15").
* Treaties are divided only by explicit "Article N" headings; their numbered paragraphs
  ("1. Each Contracting Party...") stay inside the article.
* India Code's front-page "List of amending Acts" is not mistaken for sections.
* Lines the PDF loader marked as footnotes (small font, prefixed "† ") are never headings.
* Articles inside an Annex are cited with the annex ("Annex II, Article 3"), and in treaties
  "Section N" group titles (e.g. in TRIPS) are folded into the next article.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingest.loaders import FOOTNOTE_MARK, PageText

# What a bare numbered heading ("12. Title") is called, by manifest doc_type
DEFAULT_LABELS: dict[str, str | None] = {
    "statute": "Section",
    "rules": "Rule",
    "treaty": None,  # treaties use explicit "Article N" headings; numbered lines are paragraphs
    "guideline": "Para",
    "registry_note": "Para",
}

_FOOTNOTE_PREFIX = r"(?:\d{1,2}\s?\[)?"  # India Code amendment marker, e.g. "1[3A. …"
_NUM = r"(?P<num>\d{1,3}(?:\.\d{1,3})*[A-Z]{0,3}(?:[ -]?(?:bis|ter|quater))?|[IVXLC]{1,7}(?:-?[A-Z](?![a-z]))?)"
# After the number: end of line, or optional punctuation followed by a Capitalised title
_TITLE_TAIL = r"(?:\s*$|\s*[.:\-–—]*\s*(?=[A-Zऀ-ॿ(\[\"'“]))"

_EXPLICIT = [
    ("section", "Section", r"(?:Section|SECTION|Sec\.)"),
    ("section", "Article", r"(?:Article|ARTICLE|Art\.)"),
    ("section", "Rule", r"(?:Rule|RULE)"),
    ("section", "Regulation", r"(?:Regulation|REGULATION)"),
    ("chapter", "Chapter", r"(?:Chapter|CHAPTER)"),
    ("chapter", "Part", r"(?:Part|PART)"),
    ("section", "Annex", r"(?:Annex|ANNEX|Annexure|ANNEXURE)"),
    ("section", "Appendix", r"(?:Appendix|APPENDIX)"),
]
_EXPLICIT_RE = [
    (kind, label, re.compile(rf"^{_FOOTNOTE_PREFIX}{pattern}\s+{_NUM}{_TITLE_TAIL}"))
    for kind, label, pattern in _EXPLICIT
]

_NUMBERED_RE = re.compile(rf"^{_FOOTNOTE_PREFIX}(?P<num>\d{{1,3}}[A-Z]{{0,3}})\.\s+(?=[A-Zऀ-ॿ(\[\"'“])")
_NUMBERED_MULTI_RE = re.compile(r"^(?P<num>\d{1,3}(?:\.\d{1,3}){1,3})\.?\s+(?=[A-Zऀ-ॿ])")

_ORDINALS = "FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH"
_SCHEDULE_RE = re.compile(
    rf"^{_FOOTNOTE_PREFIX}(?:THE\s+|The\s+)?(?:(?P<ord>{_ORDINALS}|{_ORDINALS.title()})\s+)?(?:SCHEDULE|Schedule)"
    r"(?:\s+(?P<num>[A-Z]{1,2}\(\d{1,2}\)|[IVXLC]{1,6}|[A-Z]{1,2}|\d{1,3}))?"
    r"\s*[.:\-–—]?\s*(?:[(\[][^)\]]{0,80}[)\]])?\s*$"
)
_TOC_RE = re.compile(
    r"^(?:ARRANGEMENT OF (?:SECTIONS|RULES|REGULATIONS|CLAUSES|ARTICLES)|TABLE OF CONTENTS|CONTENTS"
    r"|Arrangement of (?:Sections|Rules|Regulations|Clauses|Articles)|Table of Contents|Contents)\s*$"
)
_FOOTNOTE_RE = re.compile(
    r"^\d{1,3}\.\s*(?:Subs\.|Ins\.|Omitted|Added by|Rep\.|Renumbered|Vide|The words|Certain words|w\.e\.f|Now see|Came into force)"
)
# "1. The Patents (Amendment) Act, 2005 (15 of 2005)." — India Code's list of amending Acts
_AMENDING_ACT_RE = re.compile(r"^\d{1,3}\.\s+The\s.+\(\s*(?:Act\s+(?:No\.\s*)?)?\d+\s+of\s+\d{4}")
_KEYWORD_ONLY_RE = re.compile(r"^(?:Article|ARTICLE|Section|SECTION|Rule|RULE|Chapter|CHAPTER|Part|PART|Annex|ANNEX)$")
_NUMBER_ONLY_RE = re.compile(r"^(?:\d{1,3}[A-Z]{0,2}|[IVXLC]{1,7})\.?$")
_BARE_HEADING_RE = re.compile(r"^\S+\s+\S+?[.:]?$")  # keyword + number and nothing else
_SENTENCE_BOUNDARY_RE = re.compile(r"[.:;!?)\]\"”’—–-]$")
_CLAUSE_RE = re.compile(r"^\((?P<label>[a-z]{1,4}|\d{1,3}[A-Z]?)\)")
_SENTENCE_END_RE = re.compile(r"(?<=[.;:!?।])\s+")


def estimate_tokens(text: str) -> int:
    """Rough token count (≈1.3 tokens per word) — good enough for sizing chunks."""
    return max(1, int(len(text.split()) * 1.3))


@dataclass(frozen=True)
class ChunkDraft:
    ordinal: int
    section_ref: str
    heading: str
    kind: str  # provision | preamble | toc
    text: str
    page: int
    token_estimate: int


@dataclass(frozen=True)
class _Heading:
    kind: str  # section | chapter | schedule | toc
    ref: str
    number: int | None
    numbered: bool = False  # a bare "12." heading (subject to the monotonic check)


@dataclass
class _Section:
    ref: str
    kind: str  # provision | preamble | toc | chapter
    heading: str
    lines: list[tuple[int, str]] = field(default_factory=list)

    def text(self) -> str:
        return _join(self.lines)


@dataclass
class _Unit:
    page: int
    text: str
    label: str | None = None
    primary: str | None = None


def _join(lines: list[tuple[int, str]]) -> str:
    return "\n".join(text for _, text in lines).strip()


def _leading_int(num: str) -> int | None:
    match = re.match(r"\d+", num)
    return int(match.group()) if match else None


class _HeadingDetector:
    """Stateful: remembers whether we're in a table of contents or a schedule, and the last section number."""

    def __init__(self, numbered_label: str | None, treaty: bool = False) -> None:
        self.numbered_label = numbered_label
        self.treaty = treaty
        self.annex: str | None = None
        self.annex_part: str | None = None
        self.in_toc = False
        self.toc_numbers_seen = 0
        self.in_schedule = False
        self.sections_seen = 0
        self.last_number: int | None = None

    def detect(self, line: str, previous: str = "") -> _Heading | None:
        if _TOC_RE.match(line):
            self.in_toc, self.toc_numbers_seen, self.in_schedule = True, 0, False
            return _Heading("toc", "Arrangement of sections", None)
        if line.startswith(FOOTNOTE_MARK) or _FOOTNOTE_RE.match(line) or _AMENDING_ACT_RE.match(line):
            return None

        heading = self._explicit(line)
        if heading and _BARE_HEADING_RE.match(line.strip()) and not _ends_sentence(previous):
            return None  # a wrapped cross-reference, e.g. "...in accordance with / Article 15"
        if heading is None and not self.in_toc and self.sections_seen:
            heading = self._schedule(line)  # a Schedule only after the provisions have started
        if heading is None and not self.in_schedule and self.numbered_label:
            heading = self._numbered(line)
        if heading is None:
            return None

        if self.in_toc:
            # The contents list ends when numbering restarts at 1 (the real first provision)
            if heading.number == 1 and self.toc_numbers_seen >= 2:
                self.in_toc, self.last_number = False, None
            else:
                if heading.number is not None:
                    self.toc_numbers_seen += 1
                return None

        if heading.kind == "schedule":
            self.in_schedule = True
        elif heading.kind == "section" and not heading.numbered:
            self.in_schedule = False

        if heading.numbered and heading.number is not None:
            if self.last_number is not None and heading.number < self.last_number:
                return None  # numbering went backwards: a footnote or list item, not a section
            self.last_number = heading.number
        if heading.kind == "section":
            self.sections_seen += 1
        return heading

    def _explicit(self, line: str) -> _Heading | None:
        for kind, label, regex in _EXPLICIT_RE:
            match = regex.match(line)
            if not match:
                continue
            num = match.group("num").strip()
            if label in ("Annex", "Appendix") and self.sections_seen:
                # An annex after the main text: its articles are cited as "Annex II, Article 3".
                # (A document that *is* an annex, like TRIPS = "Annex 1C", gets no prefix.)
                self.annex, self.annex_part = f"{label} {num}", None
                return _Heading(kind, self.annex, _leading_int(num))
            if label == "Part" and self.annex:
                self.annex_part = f"Part {num}"
            if self.treaty and label == "Section":
                kind = "chapter"  # a group title within a Part (e.g. TRIPS), not a provision
            ref = f"{label} {num}"
            if self.annex and label == "Article":
                ref = ", ".join(x for x in (self.annex, self.annex_part, ref) if x)
            return _Heading(kind, ref, _leading_int(num))
        return None

    def _schedule(self, line: str) -> _Heading | None:
        if len(line) > 120:
            return None
        match = _SCHEDULE_RE.match(line)
        if not match:
            return None
        ordinal, num = match.group("ord"), match.group("num")
        if ordinal:
            ref = f"{ordinal.title()} Schedule" + (f" {num}" if num else "")
        else:
            ref = f"Schedule {num}" if num else "Schedule"
        return _Heading("schedule", ref, None)

    def _numbered(self, line: str) -> _Heading | None:
        assert self.numbered_label
        match = _NUMBERED_RE.match(line) or _NUMBERED_MULTI_RE.match(line)
        if not match:
            return None
        num = match.group("num")
        return _Heading("section", f"{self.numbered_label} {num}", _leading_int(num), numbered=True)


def _ends_sentence(previous: str) -> bool:
    """True if a heading may start after this line (blank, page number, all-caps title, or sentence end)."""
    previous = previous.strip()
    return (
        not previous
        or previous.isdigit()
        or bool(re.fullmatch(r"page\s+\d+", previous, flags=re.IGNORECASE))  # running page header
        or (previous.isupper() and len(previous) > 3)
        or bool(_SENTENCE_BOUNDARY_RE.search(previous))
        or _is_title_line(previous)
    )


def _is_title_line(line: str) -> bool:
    """A short Title Case line such as "Access to Genetic Resources" (a heading's title, not running text)."""
    words = line.split()
    long_words = [w for w in words if len(w) > 3]
    return 0 < len(words) <= 10 and bool(long_words) and all(w[0].isupper() for w in long_words)


def _join_split_headings(lines: list[str]) -> list[str]:
    """PDF layouts often put "Article" and "15" on separate lines; join them into "Article 15"."""
    joined: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        following = next((j for j in range(index + 1, min(index + 3, len(lines))) if lines[j].strip()), None)
        if (
            _KEYWORD_ONLY_RE.match(line.strip())
            and following is not None
            and _NUMBER_ONLY_RE.match(lines[following].strip())
        ):
            joined.append(f"{line.strip()} {lines[following].strip().rstrip('.')}")
            index = following + 1
            continue
        joined.append(line)
        index += 1
    return joined


def _split_sections(pages: list[PageText], numbered_label: str | None, treaty: bool = False) -> list[_Section]:
    detector = _HeadingDetector(numbered_label, treaty)
    sections: list[_Section] = []
    current = _Section("Preamble", "preamble", "")
    previous = ""
    for page in pages:
        for line in _join_split_headings(page.text.split("\n")):
            if not line.strip():
                current.lines.append((page.page, ""))
                continue
            heading = detector.detect(line, previous)
            previous = "" if heading else line  # a heading may directly follow another heading
            if heading is None:
                current.lines.append((page.page, line))
                continue
            carried: list[tuple[int, str]] = []
            if current.kind == "chapter" and estimate_tokens(current.text()) <= 40:
                carried = current.lines  # a bare "CHAPTER II / TITLE" is folded into the next provision
            else:
                sections.append(current)
            kind = {"toc": "toc", "chapter": "chapter"}.get(heading.kind, "provision")
            current = _Section(heading.ref, kind, line[:300], carried + [(page.page, line)])
    sections.append(current)

    result = []
    for section in sections:
        if not section.text():
            continue
        if section.kind == "chapter":
            section.kind = "provision"
        result.append(section)
    return result


def _units(lines: list[tuple[int, str]]) -> list[_Unit]:
    """Group body lines into paragraphs / clauses; a clause starts at a line like "(a)" or "(2)"."""
    units: list[_Unit] = []
    buffer: list[str] = []
    page, label = 0, None

    def flush() -> None:
        nonlocal buffer, label
        if buffer:
            units.append(_Unit(page, "\n".join(buffer), label))
        buffer, label = [], None

    for line_page, text in lines:
        if not text:
            flush()
            continue
        clause = _CLAUSE_RE.match(text)
        if clause:
            flush()
            label = f"({clause.group('label')})"
        if not buffer:
            page = line_page
        buffer.append(text)
    flush()
    return units


def _split_oversize(unit: _Unit, target: int, max_tokens: int) -> list[_Unit]:
    if estimate_tokens(unit.text) <= max_tokens:
        return [unit]
    pieces: list[str] = []
    for sentence in _SENTENCE_END_RE.split(unit.text):
        words = sentence.split()
        step = max(1, int(target / 1.3))
        pieces.extend(" ".join(words[i : i + step]) for i in range(0, len(words), step))
    packed: list[str] = []
    for piece in pieces:
        if packed and estimate_tokens(packed[-1] + " " + piece) <= target:
            packed[-1] = packed[-1] + " " + piece
        else:
            packed.append(piece)
    return [_Unit(unit.page, text, unit.label) for text in packed]


def _assign_primary_labels(units: list[_Unit]) -> None:
    """Track which top-level clause each unit belongs to, so a part can be cited as e.g. "(k)–(p)"."""
    labels = [u.label for u in units if u.label]
    if not labels:
        return
    primary_is_numeric = labels[0][1].isdigit()
    current: str | None = None
    for unit in units:
        if unit.label and unit.label[1].isdigit() == primary_is_numeric:
            current = unit.label
        unit.primary = current


def _part_ref(base: str, part: list[_Unit], index: int) -> str:
    primaries = [u.primary for u in part if u.primary]
    if not primaries:
        return f"{base} (part {index + 1})"
    first, last = primaries[0], primaries[-1]
    return f"{base}{first}" if first == last else f"{base}{first}–{last}"


def _tail_words(text: str, overlap_tokens: int) -> str:
    count = int(overlap_tokens / 1.3)
    return " ".join(text.split()[-count:]) if count > 0 else ""


def _pack_section(section: _Section, target: int, max_tokens: int, overlap: int) -> list[tuple[str, str, int]]:
    """Return (section_ref, text, page) parts for one section."""
    full_text = section.text()
    first_page = next((p for p, t in section.lines if t), section.lines[0][0])
    if estimate_tokens(full_text) <= max_tokens:
        return [(section.ref, full_text, first_page)]

    # Everything up to and including the heading line is the header of part 1
    head_index = next((i for i, (_, t) in enumerate(section.lines) if t and t[:300] == section.heading), -1)
    header_lines = section.lines[: head_index + 1]
    body_lines = section.lines[head_index + 1 :]
    if header_lines and estimate_tokens(header_lines[-1][1]) > 60:
        # Heading and body share one long line (common in HTML): keep the line in the body
        body_lines = header_lines[-1:] + body_lines
        header_lines = header_lines[:-1]
        short_heading = " ".join(section.heading.split()[:20]) + " …"
    else:
        short_heading = section.heading or section.ref
    header_text = _join(header_lines)

    units: list[_Unit] = []
    for unit in _units(body_lines):
        units.extend(_split_oversize(unit, target, max_tokens))
    _assign_primary_labels(units)

    parts: list[list[_Unit]] = []
    current: list[_Unit] = []
    current_tokens = 0
    for unit in units:
        tokens = estimate_tokens(unit.text)
        if current and current_tokens + tokens > target:
            parts.append(current)
            current, current_tokens = [], 0
        current.append(unit)
        current_tokens += tokens
    if current:
        last_tokens = sum(estimate_tokens(u.text) for u in parts[-1]) if parts else 0
        if parts and current_tokens < target // 4 and last_tokens + current_tokens <= max_tokens:
            parts[-1].extend(current)
        else:
            parts.append(current)

    output: list[tuple[str, str, int]] = []
    previous_tail = ""
    for index, part in enumerate(parts):
        body = "\n".join(u.text for u in part)
        head = header_text if index == 0 else f"{short_heading} (continued)"
        pieces = [head] if head else []
        if previous_tail:
            pieces.append(f"… {previous_tail}")
        pieces.append(body)
        output.append((_part_ref(section.ref, part, index), "\n".join(pieces), part[0].page))
        previous_tail = _tail_words(body, overlap)
    return output


def chunk_document(
    pages: list[PageText],
    *,
    doc_type: str,
    section_label: str | None = None,
    target_tokens: int = 600,
    max_tokens: int = 800,
    overlap_tokens: int = 60,
) -> list[ChunkDraft]:
    """Split a document's pages into section-aligned chunks."""
    label = section_label or DEFAULT_LABELS.get(doc_type, "Section")  # None: no bare numbered headings
    drafts: list[ChunkDraft] = []
    for section in _split_sections(pages, label, treaty=doc_type == "treaty"):
        for ref, text, page in _pack_section(section, target_tokens, max_tokens, overlap_tokens):
            drafts.append(
                ChunkDraft(
                    ordinal=len(drafts),
                    section_ref=ref,
                    heading=section.heading or section.ref,
                    kind=section.kind,
                    text=text,
                    page=page,
                    token_estimate=estimate_tokens(text),
                )
            )
    return drafts

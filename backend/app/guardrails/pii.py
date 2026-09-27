"""PII scrubber: masks emails, phone numbers and Indian ID numbers.

It runs before a query is logged and before it is sent to the LLM, so personal data
never leaves the machine or reaches the audit log. Side effect: long ID-like numbers
(including some patent application numbers) are masked too. That's acceptable, because
AyuPramana gives general information, not case-specific advice.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    # Aadhaar: 12 digits, first digit 2-9, optionally grouped 4-4-4
    ("AADHAAR", re.compile(r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")),
    # PAN: 5 letters, 4 digits, 1 letter
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    # Indian mobile numbers with optional +91 / 0091 / 0 prefix
    ("PHONE", re.compile(r"(?<!\d)(?:(?:\+|00)91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")),
    # Other international numbers written with a leading +
    ("PHONE", re.compile(r"\+\d{1,3}[\s-]?\d[\d\s-]{6,14}\d")),
    # Any remaining long digit run (bank accounts, other IDs)
    ("ID_NUMBER", re.compile(r"(?<!\d)\d{9,18}(?!\d)")),
]


@dataclass
class ScrubResult:
    text: str
    found: Counter = field(default_factory=Counter)

    @property
    def had_pii(self) -> bool:
        return bool(self.found)


def scrub(text: str) -> ScrubResult:
    """Replace personal data with placeholders like [EMAIL] or [PHONE]."""
    found: Counter = Counter()
    for label, pattern in _PATTERNS:
        text, count = pattern.subn(f"[{label}]", text)
        if count:
            found[label] += count
    return ScrubResult(text, found)

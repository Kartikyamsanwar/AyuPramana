"""Load and validate `data/manifest.yaml` — the list of documents the corpus may contain."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

JURISDICTIONS = ("india", "international")
DOMAINS = ("ip", "abs", "drug_regulation", "advertising", "food", "cosmetics", "tk")
DOC_TYPES = ("statute", "rules", "treaty", "guideline", "registry_note")

Jurisdiction = Literal["india", "international"]
Domain = Literal["ip", "abs", "drug_regulation", "advertising", "food", "cosmetics", "tk"]
DocType = Literal["statute", "rules", "treaty", "guideline", "registry_note"]


class ManifestError(ValueError):
    """The manifest file is malformed; the message says which entry and field."""


class ManifestEntry(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$", max_length=100)
    title: str = Field(min_length=3)
    jurisdiction: Jurisdiction
    domain: Domain
    doc_type: DocType
    version_date: str
    source_url: str = ""
    file: str
    # Optional: what numbered headings are called in this document ("Section", "Rule", "Regulation", "Article"…).
    # Defaults by doc_type — see ingest/chunker.py.
    section_label: str | None = None

    @field_validator("version_date")
    @classmethod
    def _iso_date(cls, value: str) -> str:
        value = str(value)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("version_date must be YYYY-MM-DD (copy it from the document)")
        date.fromisoformat(value)
        return value

    @field_validator("file")
    @classmethod
    def _relative_file(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("file must be a path inside data/raw/, e.g. india/patents_act_1970.pdf")
        return path.as_posix()


def load_manifest(path: Path) -> list[ManifestEntry]:
    """Parse the manifest. An empty or all-comment file is a valid, empty corpus."""
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"{path.name} is not valid YAML: {exc}") from exc
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ManifestError(f"{path.name} must be a list of entries (each starting with '- id: ...')")

    entries: list[ManifestEntry] = []
    seen: set[str] = set()
    for index, item in enumerate(raw, start=1):
        try:
            entry = ManifestEntry.model_validate(item)
        except ValidationError as exc:
            label = item.get("id", f"#{index}") if isinstance(item, dict) else f"#{index}"
            raise ManifestError(f"Manifest entry {label}: {exc}") from exc
        if entry.id in seen:
            raise ManifestError(f"Manifest entry id '{entry.id}' appears twice")
        seen.add(entry.id)
        entries.append(entry)
    return entries

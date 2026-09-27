"""Curated portal links (data/registry_links.yaml). Only `verified: true` entries are ever shown."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)

# Words in a question that point at a topic
TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "patent": ("patent", "invention", "pct"),
    "trademark": ("trademark", "trade mark", "brand", "logo", "madrid"),
    "design": ("design", "packaging shape", "hague"),
    "gi": ("geographical indication", " gi ", "gi tag"),
    "copyright": ("copyright", "book", "manuscript", "software", "label artwork"),
    "plant_variety": ("plant variety", "seed variety", "breeder", "farmers' rights", "farmers rights"),
    "abs": ("benefit shar", "biological resource", "biodiversity", " abs ", "access and benefit", "nba"),
    "tk": ("traditional knowledge", "tkdl"),
    "prior_art_search": ("prior art", "tkdl", "novelty", "search"),
    "drug_licence": ("drug licen", "manufacturing licen", "licence to manufacture", "license to manufacture"),
    "food": ("food", "aahar", "nutraceutical", "supplement", "fssai"),
    "cosmetics": ("cosmetic", "skin", "hair", "beauty"),
}

INTENT_TOPICS = {
    "ip_protection": ["patent", "trademark", "design", "gi", "copyright", "plant_variety"],
    "abs_compliance": ["abs"],
    "prior_art_tk": ["prior_art_search", "tk"],
}


class RegistryLink(BaseModel):
    id: str
    name: str
    jurisdiction: Literal["india", "international"]
    topics: list[str]
    url: str = ""
    note: str = ""
    verified: bool = False


def load_registry_links(path: Path) -> list[RegistryLink]:
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        return [RegistryLink.model_validate(item) for item in raw]
    except (yaml.YAMLError, ValidationError, TypeError) as exc:
        log.error("registry_links.yaml is invalid: %s", exc)
        return []


def topics_for(question: str, intents: list[str] | None = None) -> set[str]:
    text = f" {question.lower()} "
    topics = {topic for topic, words in TOPIC_KEYWORDS.items() if any(w in text for w in words)}
    if not topics:
        for intent in intents or []:
            topics.update(INTENT_TOPICS.get(intent, []))
    return topics


def verified_links(links: list[RegistryLink], jurisdiction: str, topics: set[str]) -> list[RegistryLink]:
    return [
        link
        for link in links
        if link.verified
        and re.match(r"^https://", link.url)
        and link.jurisdiction == jurisdiction
        and topics.intersection(link.topics)
    ]


def links_markdown(links: list[RegistryLink], heading: str) -> str:
    lines = [f"**{heading}**", ""]
    for link in links:
        note = f" — {link.note}" if link.note else ""
        lines.append(f"- [{link.name}]({link.url}){note}")
    return "\n".join(lines)

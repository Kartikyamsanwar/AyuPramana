"""Fixed texts the assistant shows: the disclaimer, abstention and scope messages.

Keeping them here (not in prompts) guarantees they are always present, identical
and never altered by the LLM. Add a language by adding a column to each entry.
"""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "disclaimer": {
        "en": "This is information, not legal advice.",
    },
    "abstain_no_sources": {
        "en": "I couldn't find anything in the loaded documents for this jurisdiction that answers your "
        "question, so I won't guess. You can rephrase, or talk to an IP facilitator.",
    },
    "abstain_insufficient": {
        "en": "The documents I retrieved don't clearly answer this question, so I won't guess. "
        "An IP facilitator can help you with it.",
    },
    "abstain_low_confidence": {
        "en": "I found some possibly related provisions, but I'm not confident enough that they answer your "
        "question. Please check the sources below or talk to an IP facilitator.",
    },
    "abstain_no_corpus": {
        "en": "No documents have been loaded for this jurisdiction yet, so I can't answer. "
        "(Administrators: add documents to data/raw/ and run the ingest script.)",
    },
    "extractive_intro": {
        "en": "The AI writer is unavailable right now, so here are the most relevant provisions, quoted from the "
        "sources:",
    },
}


def msg(key: str, language: str = "en") -> str:
    """Look up a fixed message, falling back to English."""
    entry = MESSAGES[key]
    return entry.get(language) or entry["en"]

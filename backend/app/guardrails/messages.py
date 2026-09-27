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
    "abstain_unsupported": {
        "en": "I drafted an answer, but my fact-check could not confirm it against the sources, so I've withheld "
        "it. Please check the related provisions below or talk to an IP facilitator.",
    },
    "possibly_related": {
        "en": "Possibly related provisions you can read:",
    },
    "escalation_recorded": {
        "en": "Your request for an IP facilitator has been recorded (reference {reference}). Quote this reference "
        "when you contact the IP facilitation desk. Please don't share personal details in this chat.",
    },
    "out_of_scope_medical": {
        "en": "I can't help with medical, dosage or treatment questions — please consult a qualified Ayurveda "
        "practitioner. I can answer questions about intellectual property and regulatory rules for Ayurvedic products.",
    },
    "off_topic": {
        "en": "That's outside what I can help with. I answer questions about intellectual property (patents, trade "
        "marks, GI, designs, copyright, plant varieties), access and benefit sharing, traditional knowledge, and "
        "regulatory approvals for Ayurvedic products.",
    },
    "greeting": {
        "en": "Namaste! I explain intellectual-property and regulatory rules for Ayurvedic products, citing the exact "
        "provision each answer comes from. Try one of these, or ask your own question:",
    },
    "legal_advice_notice": {
        "en": "I can't advise on your specific situation or dispute. Below is general information from the sources; "
        "for your case, please talk to an IP facilitator.",
    },
    "flow_intro": {
        "en": "Let's work out your product's regulatory category. I'll ask a few quick questions.",
    },
    "flow_cancelled": {
        "en": "Okay, I've stopped the product classification. Ask me anything else.",
    },
    "partial_answer": {
        "en": "I couldn't answer the part about {topics} from the loaded sources.",
    },
    "links_heading": {
        "en": "Official portals (team-verified list):",
    },
    "links_not_verified": {
        "en": "_Official portal links for this topic haven't been verified by the team yet._",
    },
    "agent_formulation_classification": {"en": "Product category"},
    "agent_ip_protection": {"en": "Intellectual property"},
    "agent_abs_compliance": {"en": "Access & benefit sharing"},
    "agent_prior_art_tk": {"en": "Traditional knowledge & prior art"},
    "agent_registry_navigation": {"en": "Where to apply"},
    "agent_general_regulatory": {"en": "Regulatory information"},
    "starter_patent": {"en": "Can I patent a classical Ayurvedic formulation?"},
    "starter_plant": {"en": "What approvals do I need to use a medicinal plant commercially?"},
    "starter_classify": {"en": "Which regulatory category does my herbal product fall into?"},
    "extractive_intro": {
        "en": "The AI writer is unavailable right now, so here are the most relevant provisions, quoted from the "
        "sources:",
    },
}


def msg(key: str, language: str = "en") -> str:
    """Look up a fixed message, falling back to English."""
    entry = MESSAGES[key]
    return entry.get(language) or entry["en"]

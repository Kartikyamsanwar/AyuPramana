"""Confidence scoring, citation verification, abstention and escalation."""

from sqlalchemy import select

from app.db.models import Escalation
from app.guardrails import confidence as conf
from app.guardrails.verification import remove_statements, split_statements
from app.llm.base import LLMError
from tests.conftest import FakeLLM, verification_json
from tests.test_chat_api import ask

THREE_CLAIMS = (
    "Widgets must be registered with the registrar. [S1]\n"
    "- Registration is renewed every seven moons. [S1]\n"
    "- Unregistered widgets are fined a hundred gold coins. [S2]"
)


def test_confidence_formula_and_unverified_cap() -> None:
    assert conf.combine(conf.ConfidenceSignals(1.0, 1.0, 1.0)) == 1.0
    assert conf.combine(conf.ConfidenceSignals(0.5, 0.0, 1.0)) == round(0.45 * 0.5 + 0.40, 3)
    # Without verification an answer can never reach "High"
    assert conf.combine(conf.ConfidenceSignals(1.0, 1.0, None)) == conf.UNVERIFIED_CAP


def test_split_and_remove_statements() -> None:
    markdown = "Key points:\n" + THREE_CLAIMS + "\nA closing sentence without any citation at all."
    statements = split_statements(markdown)
    assert [s.id for s in statements] == [1, 2, 3, 4]
    assert statements[2].text.endswith("[S2]")
    cleaned = remove_statements(markdown, [statements[2], statements[3]])
    assert "gold coins" not in cleaned and "closing sentence" not in cleaned
    assert "seven moons" in cleaned and cleaned.startswith("Key points:")


def test_unsupported_statement_is_removed(make_client) -> None:
    llm = FakeLLM(answer=THREE_CLAIMS, json_responder=lambda s, user, kw: verification_json(user, unsupported={3}))
    client, _ = make_client(llm=llm)
    block = ask(client)["answers"]["india"]
    assert not block["abstained"]
    assert "gold coins" not in block["markdown"]
    assert block["signals"]["verification"] == round(2 / 3, 3)


def test_mostly_unsupported_answer_abstains_with_related_sources(make_client) -> None:
    llm = FakeLLM(answer=THREE_CLAIMS, json_responder=lambda s, user, kw: verification_json(user, unsupported={1, 2, 3}))
    client, _ = make_client(llm=llm)
    block = ask(client)["answers"]["india"]
    assert block["abstained"] and block["abstain_reason"] == "unsupported"
    assert block["escalation_suggested"]
    assert block["citations"], "related provisions are offered as pointers"
    assert "Possibly related provisions" in block["markdown"]


def test_low_confidence_abstains(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(), confidence_threshold=0.99)
    block = ask(client)["answers"]["india"]
    assert block["abstained"] and block["abstain_reason"] == "low_confidence"
    assert block["confidence_label"] == "low"


def test_verification_failure_caps_confidence(make_client) -> None:
    def broken(*_):
        raise LLMError("verifier down")

    client, _ = make_client(llm=FakeLLM(json_responder=broken), confidence_threshold=0.1)
    block = ask(client)["answers"]["india"]
    assert not block["abstained"]
    assert block["confidence"] <= conf.UNVERIFIED_CAP
    assert block["confidence_label"] != "high"
    assert "verification" not in block["signals"]


def test_hybrid_search_marks_both_retrievers(make_services) -> None:
    services = make_services()
    hits = services.retriever.search("renewal of widget registration seven moons", "india")
    assert hits[0].chunk.section_ref == "Section 4"
    assert hits[0].in_bm25 and hits[0].in_vector
    assert all(0.0 <= h.relevance <= 1.0 for h in hits)


def test_reranker_sets_relevance_and_order(make_services) -> None:
    from tests.conftest import FakeReranker

    services = make_services(reranker=FakeReranker())
    hits = services.retriever.search("grove keepers sea shells", "india")
    assert hits[0].chunk.doc_id == "starlight_rules"
    assert hits[0].rerank_score is not None and hits[0].relevance == hits[0].rerank_score
    assert [h.rerank_score for h in hits] == sorted([h.rerank_score for h in hits], reverse=True)


def test_escalation_is_recorded_without_pii(make_client) -> None:
    client, services = make_client(llm=FakeLLM())
    query_id = ask(client)["query_id"]
    response = client.post(
        "/api/escalate",
        json={
            "session_id": "test-session-0001",
            "query_id": query_id,
            "jurisdiction": "india",
            "note": "Please call me on 9876543210",
        },
    )
    body = response.json()
    assert response.status_code == 200 and body["status"] == "recorded"
    assert body["reference"].startswith("ESC-") and body["reference"] in body["message"]
    with services.session_factory() as session:
        row = session.scalars(select(Escalation)).one()
    assert row.query_id == query_id and "9876543210" not in row.note

"""/api/chat: citations, jurisdiction separation, abstention and extractive fallback."""

import json

from sqlalchemy import select, update

from app.db.models import Chunk, QueryLog
from tests.conftest import FakeLLM

SESSION = "test-session-0001"


def ask(client, message="How are widgets registered?", jurisdiction="india", language="en"):
    response = client.post(
        "/api/chat",
        json={"session_id": SESSION, "message": message, "jurisdiction": jurisdiction, "language": language},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_answer_has_citations_and_disclaimer(make_client) -> None:
    client, _ = make_client(llm=FakeLLM())
    body = ask(client)
    block = body["answers"]["india"]
    assert body["disclaimer"] == "This is information, not legal advice."
    assert not block["abstained"]
    assert "[S1]" in block["markdown"]
    citation = block["citations"][0]
    assert citation["marker"] == 1
    assert citation["jurisdiction"] == "india"
    assert {"doc_title", "section_ref", "version_date", "source_url", "snippet"} <= set(citation)


def test_both_returns_two_separate_blocks(make_client) -> None:
    client, _ = make_client(llm=FakeLLM())
    body = ask(client, jurisdiction="both")
    assert set(body["answers"]) == {"india", "international"}
    for key, block in body["answers"].items():
        assert {c["jurisdiction"] for c in block["citations"]} <= {key}


def test_insufficient_evidence_abstains(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(lambda *_: "INSUFFICIENT_EVIDENCE"))
    block = ask(client)["answers"]["india"]
    assert block["abstained"] and block["abstain_reason"] == "insufficient_evidence"
    # Sources are offered only as clearly labelled pointers, never as an answer
    assert block["markdown"].startswith("The documents I retrieved don't clearly answer")
    assert "Possibly related provisions" in block["markdown"]


def test_answer_without_citations_abstains(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(lambda *_: "Widgets are registered."))
    block = ask(client)["answers"]["india"]
    assert block["abstained"] and block["abstain_reason"] == "no_citations"


def test_invented_marker_is_dropped(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(lambda *_: "Registration is needed. [S99] Renewal applies. [S2]"))
    block = ask(client)["answers"]["india"]
    assert "[S99]" not in block["markdown"]
    assert "[S1]" in block["markdown"]  # [S2] renumbered to [S1]
    assert len(block["citations"]) == 1


def test_no_llm_falls_back_to_quoting_sources(make_client) -> None:
    client, _ = make_client(llm=None, confidence_threshold=0.2)
    block = ask(client, "registration of widgets registrar application")["answers"]["india"]
    assert block["mode"] == "extractive"
    assert block["citations"]
    assert block["confidence"] <= 0.74  # quotes are unverified, so never "High"


def test_empty_jurisdiction_abstains(make_client) -> None:
    client, services = make_client(llm=FakeLLM())
    # Retire every international chunk: that jurisdiction now has no corpus
    with services.session_factory() as session:
        session.execute(update(Chunk).where(Chunk.jurisdiction == "international").values(is_active=False))
        session.commit()
    block = ask(client, jurisdiction="international")["answers"]["international"]
    assert block["abstained"]


def test_query_is_logged_without_pii(make_client) -> None:
    client, services = make_client(llm=FakeLLM())
    body = ask(client, message="I am vaidya@example.com — how are widgets registered?")
    with services.session_factory() as session:
        row = session.scalars(select(QueryLog).where(QueryLog.id == body["query_id"])).one()
    assert "example.com" not in row.query_text and "[EMAIL]" in row.query_text
    assert "india" in json.loads(row.blocks_summary)


def test_sources_lists_manifest_status(make_client) -> None:
    client, _ = make_client()
    documents = {d["id"]: d for d in client.get("/api/sources").json()["documents"]}
    assert documents["widgets_act"]["status"] == "ingested"
    assert documents["widgets_act"]["active_version"]["chunk_count"] > 0
    assert documents["missing_doc"]["status"] == "missing_file"


def test_invalid_request_is_rejected(make_client) -> None:
    client, _ = make_client()
    response = client.post("/api/chat", json={"session_id": "x", "message": "", "jurisdiction": "mars"})
    assert response.status_code == 422


def test_loose_marker_formats_are_normalised(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(answer="Widgets are registered with the registrar [ S1 ]. Renewal applies [s2, S3]."))
    block = ask(client)["answers"]["india"]
    assert "[S1]" in block["markdown"] and "[ S1 ]" not in block["markdown"]
    assert len(block["citations"]) == 3

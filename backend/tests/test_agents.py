"""Router, specialists, composer, formulation flow and streaming."""

import json

import yaml

from app.agents.router import Router, keyword_route
from tests.conftest import FakeLLM, routing_responder
from tests.test_chat_api import SESSION, ask


def post(client, **body):
    payload = {"session_id": SESSION, "language": "en", "jurisdiction": "india", **body}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


# --- Router ---------------------------------------------------------------
def test_keyword_router() -> None:
    assert keyword_route("Namaste!").scope == "greeting"
    assert keyword_route("What dosage of ashwagandha should I take?").scope == "medical_advice"
    assert keyword_route("Should I sue the company copying my brand?").scope == "personal_legal_advice"
    assert keyword_route("Can I patent my formulation?").intents == ["ip_protection"]
    assert keyword_route("Do I need NBA approval for benefit sharing?").intents[0] == "abs_compliance"
    assert "prior_art_tk" in keyword_route("Is TKDL prior art?").intents
    assert keyword_route("Tell me about widgets").intents == ["general_regulatory"]


def test_llm_router_validates_json_and_falls_back() -> None:
    llm = FakeLLM(json_responder=routing_responder("in_scope", ["abs_compliance", "made_up", "ip_protection", "x"]))
    route = Router(llm).route("question")
    assert route.method == "llm" and route.intents == ["abs_compliance", "ip_protection"]

    broken = FakeLLM(json_responder=lambda *_: "not json")
    assert Router(broken).route("Can I patent this?").method == "keywords"


# --- Scope handling ---------------------------------------------------------
def test_medical_question_abstains_without_drafting(make_client) -> None:
    llm = FakeLLM(json_responder=routing_responder("medical_advice"))
    client, _ = make_client(llm=llm)
    body = post(client, message="How much should I take daily?", jurisdiction="both")
    for block in body["answers"].values():
        assert block["abstained"] and block["abstain_reason"] == "out_of_scope_medical"
        assert not block["escalation_suggested"]
    assert all(kw.get("json_mode") for _, _, kw in llm.calls), "no answer should be drafted"


def test_personal_legal_advice_gives_general_info_with_notice(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("personal_legal_advice", ["ip_protection"])))
    body = post(client, message="Should I sue someone for copying my widget?")
    assert body["notice"].startswith("I can't advise on your specific situation")
    assert body["answers"]["india"]["escalation_suggested"]


def test_greeting_offers_starters(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("greeting")))
    body = post(client, message="hello")
    assert body["answers"] == {} and body["follow_up_question"].startswith("Namaste")
    assert len(body["quick_replies"]) == 3


# --- Composer ---------------------------------------------------------------
def test_two_specialists_are_merged_with_renumbered_citations(make_client) -> None:
    answer = "Point from the sources. [S2] Another point. [S1]"
    llm = FakeLLM(answer=answer, json_responder=routing_responder("in_scope", ["ip_protection", "abs_compliance"]))
    client, _ = make_client(llm=llm)
    block = post(client, message="widgets and starlight crystals")["answers"]["india"]
    assert block["markdown"].count("### ") == 2
    assert "### Intellectual property" in block["markdown"] and "### Access & benefit sharing" in block["markdown"]
    markers = {int(m) for m in __import__("re").findall(r"\[S(\d+)\]", block["markdown"])}
    assert markers == {c["marker"] for c in block["citations"]}
    assert len({c["chunk_id"] for c in block["citations"]}) == len(block["citations"])


# --- Registry navigator -------------------------------------------------------
def test_registry_shows_only_verified_links(make_client, settings) -> None:
    path = settings.data_dir / "registry_links.yaml"
    links = [
        {"id": "ok", "name": "Checked portal", "jurisdiction": "india", "topics": ["patent"],
         "url": "https://example.test/file", "verified": True},
        {"id": "no", "name": "Unchecked portal", "jurisdiction": "india", "topics": ["patent"],
         "url": "https://example.test/unchecked", "verified": False},
    ]
    path.write_text(yaml.safe_dump(links), encoding="utf-8")
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("in_scope", ["registry_navigation"])))
    block = post(client, message="Where do I file a patent for my widget?")["answers"]["india"]
    assert "[Checked portal](https://example.test/file)" in block["markdown"]
    assert "Unchecked portal" not in block["markdown"]


def test_registry_without_verified_links_says_so(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("in_scope", ["registry_navigation"])))
    block = post(client, message="Where do I register a widget?")["answers"]["india"]
    assert "haven't been verified by the team yet" in block["markdown"]


# --- Formulation classifier flow --------------------------------------------------
def test_formulation_flow_asks_questions_then_classifies(make_client, settings) -> None:
    llm = FakeLLM(
        answer="**Likely category:** Classical (generic) Ayurvedic medicine [S1]",
        json_responder=routing_responder("in_scope", ["formulation_classification"]),
    )
    client, _ = make_client(llm=llm)
    first = post(client, message="Which category is my herbal product?")
    assert first["answers"] == {}
    assert "(1/4)" in first["follow_up_question"]
    ids = [r["id"] for r in first["quick_replies"]]
    assert "origin:classical_text" in ids and "flow:cancel" in ids

    second = post(client, message="Exactly as described in a classical Ayurvedic text", quick_reply_id="origin:classical_text")
    assert "(2/4)" in second["follow_up_question"]
    third = post(client, message="Not sure")  # typed label instead of a click
    assert "(3/4)" in third["follow_up_question"]
    post(client, message="x", quick_reply_id="ingredients:plant_only")
    final = post(client, message="x", quick_reply_id="claims:no_claims", jurisdiction="both")

    assert set(final["answers"]) == {"india", "international"}
    assert final["answers"]["india"]["markdown"].startswith("**Likely category:**")
    drafting_prompt = [user for system, user, kw in llm.calls if not kw.get("json_mode")][0]
    assert "Exactly as described in a classical Ayurvedic text" in drafting_prompt  # facts reach the LLM


def test_formulation_flow_can_be_cancelled_or_abandoned(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("in_scope", ["formulation_classification"])))
    post(client, message="Classify my product")
    cancelled = post(client, message="Cancel", quick_reply_id="flow:cancel")
    assert cancelled["follow_up_question"].startswith("Okay, I've stopped")

    post(client, message="Classify my product")
    moved_on = post(client, message="Something completely different")  # not an option → routed normally
    assert "(2/4)" not in (moved_on["follow_up_question"] or "")


# --- Streaming ------------------------------------------------------------------
def test_stream_emits_status_block_and_done(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("in_scope", ["ip_protection"])))
    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"session_id": SESSION, "message": "How are widgets registered?", "jurisdiction": "both"},
    ) as response:
        text = "".join(response.iter_text())
    events = [line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("event: ")]
    assert events[0] == "status" and events[-1] == "done"
    assert events.count("block") == 2
    done = json.loads(text.strip().split("data: ")[-1])
    assert set(done["answers"]) == {"india", "international"}


def test_basic_chat_still_works_via_general_agent(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("in_scope", ["general_regulatory"])))
    assert not ask(client)["answers"]["india"]["abstained"]


def test_off_topic_routing_is_overruled_when_corpus_clearly_covers_it(make_client) -> None:
    client, _ = make_client(llm=FakeLLM(json_responder=routing_responder("off_topic")))
    covered = post(client, message="Renewal of registration of a widget every seven moons on payment of sea shells")
    assert not covered["answers"]["india"]["abstained"]
    unrelated = post(client, message="Who won the cricket world cup?")
    assert unrelated["answers"]["india"]["abstain_reason"] == "off_topic"

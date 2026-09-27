"""Evaluation harness, feedback and the audit/admin API."""

import json

from app.evaluation import EvalRow, evaluate, load_questions, render_report, section_matches, summarize
from tests.conftest import FakeLLM, routing_responder
from tests.test_chat_api import SESSION, ask


def test_section_matching() -> None:
    assert section_matches("Section 3", "Section 3")
    assert section_matches("Section 3", "Section 3(k)–(p)")
    assert section_matches("section 3", "Section 3 (part 2)")
    assert not section_matches("Section 3", "Section 30")


def test_questions_template_is_valid() -> None:
    from tests.conftest import REPO_DATA

    rows = load_questions(REPO_DATA / "eval" / "questions.jsonl")
    assert len(rows) >= 10
    assert {r.language for r in rows} == {"en", "hi", "mr"}
    assert any(r.expected_behavior == "abstain" for r in rows)
    assert not any(r.verified for r in rows), "template rows stay unverified until the team checks them"


def test_evaluate_and_report(make_services) -> None:
    def json_responder(system, user, kwargs):
        if "route user messages" in system:
            scope = "medical_advice" if "dosage" in user else "in_scope"
            return json.dumps({"scope": scope, "intents": ["general_regulatory"] if scope == "in_scope" else [],
                               "search_query": user.split(":", 1)[-1]})
        from tests.conftest import verification_json

        return verification_json(user)

    services = make_services(llm=FakeLLM(json_responder=json_responder))
    rows = [
        EvalRow("w1", "How is a widget registered with the registrar?", "en", "india", "answer",
                [{"doc_id": "widgets_act", "section_ref": "Section 3"}], verified=True),
        EvalRow("w2", "What dosage should I take?", "en", "both", "abstain"),
    ]
    outcomes = evaluate(services.chat, rows)
    summary = summarize(outcomes)
    assert summary["questions"] == 2 and summary["blocks"] == 3
    assert summary["retrieval_hit_rate"] == 1.0
    assert summary["out_of_scope_abstained"] == 1.0
    assert summary["abstention_accuracy"] == 1.0
    assert summary["citation_precision"] is not None

    report = render_report(summary, outcomes, {"LLM": "fake"})
    assert "Retrieval hit rate" in report and "| w1 |" in report and "| w2 * |" in report

    # Evaluation runs are logged as source=eval and kept out of the audit stats
    overview = services.audit.overview()
    assert overview.stats.queries == 0
    assert services.audit.overview(include_eval=True).stats.queries == 2


def test_feedback_is_recorded_scrubbed(make_client) -> None:
    client, services = make_client(llm=FakeLLM(json_responder=routing_responder("in_scope", ["general_regulatory"])),
                                   admin_mode=True)
    query_id = ask(client)["query_id"]
    response = client.post(
        "/api/feedback",
        json={"session_id": SESSION, "query_id": query_id, "jurisdiction": "india", "rating": "down",
              "comment": "wrong section, mail me at a@b.co"},
    )
    assert response.json() == {"status": "recorded"}
    overview = client.get("/api/admin/overview").json()
    assert overview["stats"]["feedback_down"] == 1
    assert overview["feedback"][0]["comment"] == "wrong section, mail me at [EMAIL]"
    assert overview["queries"][0]["id"] == query_id
    assert overview["stats"]["by_language"] == {"en": 1}


def test_admin_is_hidden_unless_enabled(make_client) -> None:
    client, _ = make_client()
    assert client.get("/api/admin/overview").status_code == 404
    assert client.get("/api/health").json()["features"]["admin_mode"] is False

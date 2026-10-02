"""Translation: marker preservation, Bhashini protocol, fallbacks and the Hindi/Marathi chat path."""

import json

import httpx
import pytest

from app.translate.base import TranslationError, check_markers, translate_markdown_by_segments
from app.translate.bhashini import BhashiniTranslator
from app.translate.factory import FallbackTranslator
from app.translate.llm_translate import LLMTranslator
from tests.conftest import FakeLLM, verification_json
from tests.test_chat_api import SESSION

MARKDOWN = (
    "### Heading text\n"
    "Widgets must be registered. [S1] Renewal is every seven moons. [S2][S3]\n"
    "- [ ] Apply to the registrar [S1]\n"
    "- [Official portal](https://example.test/x)\n"
)


class Upper:
    """A plain-text 'translator' that upper-cases, so we can see what was translated."""

    name = "upper"

    def __init__(self):
        self.batches = []

    def translate_texts(self, texts, source, target):
        self.batches.append(list(texts))
        return [t.upper() for t in texts]

    def translate_markdown(self, markdown, source, target):
        return translate_markdown_by_segments(self, markdown, source, target)


def test_segment_translation_keeps_markers_prefixes_and_links() -> None:
    upper = Upper()
    result = upper.translate_markdown(MARKDOWN, "en", "hi")
    assert result.splitlines() == [
        "### HEADING TEXT",
        "WIDGETS MUST BE REGISTERED. [S1] RENEWAL IS EVERY SEVEN MOONS. [S2][S3]",
        "- [ ] APPLY TO THE REGISTRAR [S1]",
        "- [Official portal](https://example.test/x)",
    ]
    assert len(upper.batches) == 1  # one batched call


def test_marker_check() -> None:
    check_markers("a [S1] b [S2]", "x [S2] y [S1]")
    with pytest.raises(TranslationError):
        check_markers("a [S1] b [S2]", "x [S1] y")


def test_llm_translator_rejects_lost_markers() -> None:
    good = LLMTranslator(FakeLLM(answer="अनुवाद [S1]"))
    assert good.translate_markdown("Text [S1]", "en", "hi") == "अनुवाद [S1]"
    bad = LLMTranslator(FakeLLM(answer="अनुवाद"))
    with pytest.raises(TranslationError):
        bad.translate_markdown("Text [S1]", "en", "hi")


def test_bhashini_config_then_compute_with_cache(monkeypatch) -> None:
    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append((url, json, headers))
        if url == "https://config.test":
            body = {
                "pipelineInferenceAPIEndPoint": {
                    "callbackUrl": "https://compute.test",
                    "inferenceApiKey": {"name": "Authorization", "value": "inference-key"},
                },
                "pipelineResponseConfig": [{"config": [{"serviceId": "svc-1"}]}],
            }
        else:
            body = {"pipelineResponse": [{"output": [{"target": f"T({i['source']})"} for i in json["inputData"]["input"]]}]}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    translator = BhashiniTranslator("user", "ulca-key", "pipe-1", "https://config.test")
    assert translator.translate_texts(["a", "b"], "en", "hi") == ["T(a)", "T(b)"]
    assert translator.translate_texts(["c"], "en", "hi") == ["T(c)"]

    config_calls = [c for c in calls if c[0] == "https://config.test"]
    assert len(config_calls) == 1  # cached per language pair
    assert config_calls[0][2] == {"userID": "user", "ulcaApiKey": "ulca-key"}
    assert config_calls[0][1]["pipelineRequestConfig"] == {"pipelineId": "pipe-1"}
    compute = [c for c in calls if c[0] == "https://compute.test"][0]
    assert compute[2] == {"Authorization": "inference-key"}
    assert compute[1]["pipelineTasks"][0]["config"]["serviceId"] == "svc-1"


def test_fallback_translator_uses_next_on_failure() -> None:
    class Broken:
        name = "broken"

        def translate_texts(self, *args):
            raise TranslationError("down")

        translate_markdown = translate_texts

    chain = FallbackTranslator([Broken(), Upper()])
    assert chain.translate_texts(["x"], "en", "hi") == ["X"]


# --- Hindi end to end --------------------------------------------------------------
HINDI_QUESTION = "विजेट का पंजीकरण कैसे होता है?"


def hindi_llm(translate_ok: bool = True) -> FakeLLM:
    def text_responder(system, user, kwargs):
        if system.startswith("You translate"):
            if not translate_ok:
                return "अनुवाद बिना हवाले के"
            return "विजेट का पंजीकरण रजिस्ट्रार के पास होता है। [S1]"
        return "Widgets must be registered with the registrar. [S1]"

    def json_responder(system, user, kwargs):
        if "route user messages" in system:
            return json.dumps({"scope": "in_scope", "intents": ["general_regulatory"], "search_query": "widget registration"})
        if system.startswith("Translate each string"):
            return json.dumps({"translations": ["How are widgets registered?"]})
        return verification_json(user)

    return FakeLLM(answer=text_responder, json_responder=json_responder)


def test_hindi_question_is_pivoted_to_english_and_answer_translated(make_client) -> None:
    llm = hindi_llm()
    client, _ = make_client(llm=llm)
    body = client.post(
        "/api/chat", json={"session_id": SESSION, "message": HINDI_QUESTION, "language": "hi", "jurisdiction": "india"}
    ).json()
    block = body["answers"]["india"]
    assert block["markdown"] == "विजेट का पंजीकरण रजिस्ट्रार के पास होता है। [S1]"
    assert body["disclaimer"] == "यह जानकारी है, कानूनी सलाह नहीं।"
    # Retrieval and drafting ran on the English translation
    router_prompt = next(user for system, user, _ in llm.calls if "route user messages" in system)
    assert "How are widgets registered?" in router_prompt
    # Citation snippets stay in the source language
    assert "registration" in block["citations"][0]["snippet"].lower()


def test_failed_translation_falls_back_to_english_with_note(make_client) -> None:
    client, _ = make_client(llm=hindi_llm(translate_ok=False))
    block = client.post(
        "/api/chat", json={"session_id": SESSION, "message": HINDI_QUESTION, "language": "mr", "jurisdiction": "india"}
    ).json()["answers"]["india"]
    assert block["markdown"].startswith("_भाषांतर सध्या उपलब्ध नाही")
    assert "Widgets must be registered" in block["markdown"]


def test_untranslated_output_is_retried_on_the_main_model() -> None:
    def answer(system, user, kwargs):
        return user if kwargs.get("fast") else "अनुवाद [S1]"  # fast model echoes English back

    assert LLMTranslator(FakeLLM(answer=answer)).translate_markdown("Text [S1]", "en", "hi") == "अनुवाद [S1]"


def test_bracketed_source_annotations_are_normalised() -> None:
    from app.agents.citations import normalize_markers

    assert normalize_markers("Deceptive name【S1†L1-L4】.") == "Deceptive name[S1]."

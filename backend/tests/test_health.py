"""The health route reports configuration without leaking secrets."""

from app.config import Settings


def test_health_reports_corpus_and_llm(make_client) -> None:
    client, _ = make_client()
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["app"] == "AyuPramana"
    assert body["llm"] == {"provider": "none", "model": "", "configured": False}
    assert body["corpus"]["manifest_entries"] == 4
    assert body["corpus"]["documents"] == 3
    assert body["corpus"]["chunks"] > 0


def test_health_never_returns_api_key(make_client) -> None:
    client, _ = make_client(groq_api_key="gsk_secret_value_for_test", llm_provider="groq")
    text = client.get("/api/health").text
    assert "gsk_secret_value_for_test" not in text


def test_relative_paths_resolve_from_repo_root(tmp_path) -> None:
    settings = Settings(_env_file=None, data_dir="data", storage_dir=tmp_path)
    assert settings.data_dir.is_absolute()
    assert settings.data_dir.name == "data"
    assert settings.storage_dir == tmp_path

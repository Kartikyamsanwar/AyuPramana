"""The health route reports configuration without leaking secrets."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "AyuPramana"
    assert set(body["llm"]) == {"provider", "model", "configured"}


def test_health_never_returns_api_key(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value_for_test")
    from app import config

    config.get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        assert "gsk_secret_value_for_test" not in client.get("/api/health").text
    finally:
        config.get_settings.cache_clear()


def test_relative_paths_resolve_from_repo_root(tmp_path) -> None:
    settings = Settings(data_dir="data", storage_dir=tmp_path)
    assert settings.data_dir.is_absolute()
    assert settings.data_dir.name == "data"
    assert settings.storage_dir == tmp_path

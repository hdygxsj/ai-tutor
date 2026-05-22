from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.db.base import Base
from app.main import app


@pytest.fixture(autouse=True)
def sqlite_settings_db() -> Generator[None, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = override_get_session
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_get_tutor_settings_returns_default_fake_without_api_key() -> None:
    response = TestClient(app).get("/api/settings/tutor")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "fake"
    assert body["has_api_key"] is False
    assert "api_key" not in body


def test_put_tutor_settings_saves_openai_compatible_config_without_returning_api_key() -> None:
    client = TestClient(app)
    payload = {
        "provider": "openai_compatible",
        "base_url": "https://example.test/v1",
        "model_name": "gpt-test",
        "api_key": "secret-key",
    }

    response = client.put("/api/settings/tutor", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "provider": "openai_compatible",
        "base_url": "https://example.test/v1",
        "model_name": "gpt-test",
        "has_api_key": True,
    }
    assert "api_key" not in body

    saved_response = client.get("/api/settings/tutor")
    assert saved_response.status_code == 200
    assert saved_response.json() == body


def test_put_tutor_settings_preserves_saved_api_key_when_update_omits_it() -> None:
    client = TestClient(app)
    saved_payload = {
        "provider": "openai_compatible",
        "base_url": "https://api.example.test/v1",
        "model_name": "gpt-4o-mini",
        "api_key": "secret-key",
    }
    update_payload = {
        "provider": "openai_compatible",
        "base_url": "https://api.example.test/v1",
        "model_name": "gpt-4o-mini",
    }

    assert client.put("/api/settings/tutor", json=saved_payload).status_code == 200
    update_response = client.put("/api/settings/tutor", json=update_payload)
    saved_response = client.get("/api/settings/tutor")

    assert update_response.status_code == 200
    assert update_response.json()["has_api_key"] is True
    assert "api_key" not in update_response.json()
    assert saved_response.status_code == 200
    assert saved_response.json()["has_api_key"] is True
    assert "api_key" not in saved_response.json()


def test_test_tutor_settings_returns_ok_for_fake_provider() -> None:
    response = TestClient(app).post("/api/settings/tutor/test", json={"provider": "fake"})

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_test_tutor_settings_rejects_ollama_without_base_url() -> None:
    response = TestClient(app).post("/api/settings/tutor/test", json={"provider": "ollama"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "base_url" in body["message"]


def test_test_tutor_settings_rejects_openai_compatible_without_required_fields() -> None:
    missing_api_key = TestClient(app).post(
        "/api/settings/tutor/test",
        json={
            "provider": "openai_compatible",
            "base_url": "https://example.test/v1",
            "model_name": "gpt-test",
        },
    )
    missing_model_name = TestClient(app).post(
        "/api/settings/tutor/test",
        json={
            "provider": "openai_compatible",
            "base_url": "https://example.test/v1",
            "api_key": "secret-key",
        },
    )

    assert missing_api_key.status_code == 200
    assert missing_api_key.json()["ok"] is False
    assert "api_key" in missing_api_key.json()["message"]
    assert missing_model_name.status_code == 200
    assert missing_model_name.json()["ok"] is False
    assert "model_name" in missing_model_name.json()["message"]


def test_test_tutor_settings_uses_saved_api_key_when_payload_omits_it() -> None:
    client = TestClient(app)
    saved_payload = {
        "provider": "openai_compatible",
        "base_url": "https://api.example.test/v1",
        "model_name": "gpt-4o-mini",
        "api_key": "secret-key",
    }
    test_payload = {
        "provider": "openai_compatible",
        "base_url": "https://api.example.test/v1",
        "model_name": "gpt-4o-mini",
    }

    assert client.put("/api/settings/tutor", json=saved_payload).status_code == 200
    response = client.post("/api/settings/tutor/test", json=test_payload)

    assert response.status_code == 200
    assert response.json()["ok"] is True

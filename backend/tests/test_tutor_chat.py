from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.api.routes.settings import get_tutor_settings_service
from app.db.base import Base
from app.main import app
from app.schemas.settings import TutorSettingsUpdate
from app.services.tutor_settings_service import TutorSettingsService

SYSTEM_PROMPT = "你是 AI Dream 的机器学习导师，用中文简洁回答，并给出下一步学习建议。"


class RecordingTransport:
    def __init__(
        self,
        response: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or {}
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        self.calls.append({"url": url, "payload": payload, "headers": headers or {}})
        if self.error is not None:
            raise self.error
        return self.response


@pytest.fixture()
def tutor_settings_service() -> Generator[TutorSettingsService, None, None]:
    service = TutorSettingsService()
    app.dependency_overrides[get_tutor_settings_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.clear()


def override_chat_provider(service: TutorSettingsService, transport: RecordingTransport) -> None:
    from app.api.routes import agent as agent_routes
    from app.services.tutor_provider import TutorProviderService

    def override_tutor_provider_service() -> TutorProviderService:
        return TutorProviderService(service, transport)

    app.dependency_overrides[
        agent_routes.get_tutor_provider_service
    ] = override_tutor_provider_service


def test_agent_chat_default_fake_returns_deterministic_reply_without_creating_plan(
    tutor_settings_service: TutorSettingsService,
) -> None:
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
    client = TestClient(app)

    before_dashboard = client.get("/api/learning/dashboard")
    response = client.post("/api/agent/chat", json={"message": "我想学反向传播"})
    after_dashboard = client.get("/api/learning/dashboard")

    assert before_dashboard.status_code == 200
    assert response.status_code == 200
    assert response.json() == {
        "reply": (
            "你提到“我想学反向传播”。"
            "建议先用一个小例子写出输入、损失和梯度，再继续下一步学习。"
        ),
        "provider": "fake",
    }
    assert after_dashboard.status_code == 200
    assert after_dashboard.json() == before_dashboard.json()
    assert tutor_settings_service.get_settings().provider == "fake"


def test_agent_chat_openai_compatible_uses_mock_transport_and_parses_reply(
    tutor_settings_service: TutorSettingsService,
) -> None:
    transport = RecordingTransport(
        {
            "choices": [
                {
                    "message": {
                        "content": "先从线性回归的损失函数开始。",
                    },
                },
            ],
        },
    )
    api_key = "test-api-key"
    tutor_settings_service.save_settings(
        TutorSettingsUpdate(
            provider="openai_compatible",
            base_url="https://llm.example.test/v1",
            model_name="gpt-test",
            api_key=api_key,
        ),
    )
    override_chat_provider(tutor_settings_service, transport)

    response = TestClient(app).post(
        "/api/agent/chat",
        json={
            "message": "如何理解梯度下降？",
            "history": [{"role": "assistant", "content": "我们先看优化。"}],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "先从线性回归的损失函数开始。",
        "provider": "openai_compatible",
    }
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["url"] == "https://llm.example.test/v1/chat/completions"
    authorization = call["headers"].get("Authorization", "")
    assert authorization.startswith("Bearer ")
    assert authorization.endswith(api_key)
    assert call["payload"] == {
        "model": "gpt-test",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "我们先看优化。"},
            {"role": "user", "content": "如何理解梯度下降？"},
        ],
        "temperature": 0.2,
    }


def test_agent_chat_ollama_uses_mock_transport_and_parses_reply(
    tutor_settings_service: TutorSettingsService,
) -> None:
    transport = RecordingTransport({"message": {"content": "用链式法则拆开计算。"}})
    tutor_settings_service.save_settings(
        TutorSettingsUpdate(
            provider="ollama",
            base_url="http://localhost:11434",
            model_name="qwen2.5",
        ),
    )
    override_chat_provider(tutor_settings_service, transport)

    response = TestClient(app).post(
        "/api/agent/chat",
        json={"message": "反向传播怎么入门？"},
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "用链式法则拆开计算。", "provider": "ollama"}
    assert transport.calls == [
        {
            "url": "http://localhost:11434/api/chat",
            "headers": {},
            "payload": {
                "model": "qwen2.5",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": "反向传播怎么入门？"},
                ],
                "stream": False,
            },
        },
    ]


def test_agent_chat_missing_required_provider_settings_returns_clear_400(
    tutor_settings_service: TutorSettingsService,
) -> None:
    transport = RecordingTransport()
    tutor_settings_service.save_settings(
        TutorSettingsUpdate(provider="ollama", model_name="qwen2.5"),
    )
    override_chat_provider(tutor_settings_service, transport)

    response = TestClient(app).post("/api/agent/chat", json={"message": "你好"})

    assert response.status_code == 400
    assert "base_url" in response.json()["detail"]
    assert transport.calls == []


def test_agent_chat_transport_failure_returns_sanitized_502(
    tutor_settings_service: TutorSettingsService,
) -> None:
    transport = RecordingTransport(error=RuntimeError("Authorization: Bearer secret-key"))
    tutor_settings_service.save_settings(
        TutorSettingsUpdate(
            provider="openai_compatible",
            base_url="https://llm.example.test/v1",
            model_name="gpt-test",
            api_key="secret-key",
        ),
    )
    override_chat_provider(tutor_settings_service, transport)

    response = TestClient(app).post("/api/agent/chat", json={"message": "你好"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Tutor provider request failed."
    assert "secret-key" not in response.json()["detail"]
    assert "Authorization" not in response.json()["detail"]


def test_agent_chat_openai_malformed_content_returns_clear_502(
    tutor_settings_service: TutorSettingsService,
) -> None:
    transport = RecordingTransport({"choices": [{"message": {"content": None}}]})
    tutor_settings_service.save_settings(
        TutorSettingsUpdate(
            provider="openai_compatible",
            base_url="https://llm.example.test/v1",
            model_name="gpt-test",
            api_key="secret-key",
        ),
    )
    override_chat_provider(tutor_settings_service, transport)

    response = TestClient(app).post("/api/agent/chat", json={"message": "你好"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Tutor provider returned an invalid response."


def test_agent_chat_ollama_malformed_content_returns_clear_502(
    tutor_settings_service: TutorSettingsService,
) -> None:
    transport = RecordingTransport({"message": {"content": None}})
    tutor_settings_service.save_settings(
        TutorSettingsUpdate(
            provider="ollama",
            base_url="http://localhost:11434",
            model_name="qwen2.5",
        ),
    )
    override_chat_provider(tutor_settings_service, transport)

    response = TestClient(app).post("/api/agent/chat", json={"message": "你好"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Tutor provider returned an invalid response."

from fastapi.testclient import TestClient

from app.api.deps import get_session
from app.main import app


class FakeSession:
    def __init__(self) -> None:
        self.executed_statements = []

    def execute(self, statement) -> None:
        self.executed_statements.append(statement)


def test_health_route_returns_ok_without_real_database() -> None:
    fake_session = FakeSession()

    def override_get_session() -> FakeSession:
        return fake_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        response = TestClient(app).get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert len(fake_session.executed_statements) == 1

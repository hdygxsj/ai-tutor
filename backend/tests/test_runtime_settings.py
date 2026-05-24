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
def sqlite_runtime_settings_db() -> Generator[None, None, None]:
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


def test_runtime_settings_defaults_to_local_sandbox() -> None:
    response = TestClient(app).get("/api/runtime/settings")

    assert response.status_code == 200
    assert response.json() == {
        "backend": "sandbox",
        "sandbox_image": "python:3.12-slim",
        "kubernetes_namespace": "ai-dream-runs",
        "has_kubeconfig": False,
    }


def test_runtime_settings_accepts_kubernetes_kubeconfig_without_echoing_secret() -> None:
    client = TestClient(app)

    response = client.put(
        "/api/runtime/settings",
        json={
            "backend": "kubernetes",
            "kubeconfig": "apiVersion: v1\nclusters: []\n",
            "kubernetes_namespace": "agent-runs",
            "sandbox_image": "python:3.12-slim",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "backend": "kubernetes",
        "sandbox_image": "python:3.12-slim",
        "kubernetes_namespace": "agent-runs",
        "has_kubeconfig": True,
    }
    assert "apiVersion" not in str(response.json())


def test_runtime_settings_clears_kubeconfig_when_returning_to_sandbox() -> None:
    client = TestClient(app)
    client.put(
        "/api/runtime/settings",
        json={
            "backend": "kubernetes",
            "kubeconfig": "apiVersion: v1\nclusters: []\n",
            "kubernetes_namespace": "agent-runs",
            "sandbox_image": "python:3.12-slim",
        },
    )

    response = client.put(
        "/api/runtime/settings",
        json={
            "backend": "sandbox",
            "kubeconfig": "",
            "kubernetes_namespace": "ai-dream-runs",
            "sandbox_image": "python:3.12-slim",
        },
    )

    assert response.status_code == 200
    assert response.json()["backend"] == "sandbox"
    assert response.json()["has_kubeconfig"] is False


def test_sandbox_assignment_run_returns_recorded_logs_and_status() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={"code": "print('hello runtime')"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assignment_id"] == assignment_id
    assert payload["course_id"] == course["id"]
    assert payload["backend"] == "sandbox"
    assert payload["status"] == "completed"
    assert payload["stdout"] == "hello runtime\n"
    assert payload["stderr"] == ""
    assert payload["exit_code"] == 0
    assert payload["test_results"] == {"passed": True, "exit_code": 0}
    assert "Sandbox executed Python snippet" in payload["logs"][0]
    assert "stdout: hello runtime" in payload["logs"]
    assert payload["artifacts"] == []


def test_sandbox_assignment_run_captures_failures_without_shell_execution() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={
            "code": (
                "print('before')\n"
                "raise SystemExit(3)"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "sandbox"
    assert payload["status"] == "failed"
    assert payload["stdout"] == "before\n"
    assert payload["stderr"] == ""
    assert payload["exit_code"] == 3
    assert payload["test_results"] == {"passed": False, "exit_code": 3}
    assert payload["metadata"]["runner_type"] == "restricted_local_python_subprocess"
    assert payload["metadata"]["shell"] is False


def test_sandbox_assignment_run_blocks_dangerous_imports_before_execution() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={"code": "import os\nprint(os.environ)"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["stdout"] == ""
    assert "Import statements are not allowed" in payload["stderr"]
    assert payload["exit_code"] is None
    assert payload["metadata"]["execution"] == "blocked"
    assert "PYTHON" not in str(payload)


def test_sandbox_assignment_run_blocks_dunder_reflection_bypass() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={
            "code": (
                "name = '__' + 'class' + '__'\n"
                "print(getattr(1, name))\n"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["stdout"] == ""
    assert "not allowed" in payload["stderr"]
    assert payload["metadata"]["execution"] == "blocked"


def test_sandbox_assignment_run_blocks_private_module_escape_hatches() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={"code": "value = 1\nprint(value._hidden)"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["stdout"] == ""
    assert "Private attribute access is not allowed" in payload["stderr"]
    assert payload["metadata"]["execution"] == "blocked"


def test_sandbox_assignment_run_blocks_allowlisted_submodule_escape_hatches() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={"code": "import json.tool as tool\nprint(tool.sys.modules['os'].listdir('/'))"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["stdout"] == ""
    assert "Import statements are not allowed" in payload["stderr"]
    assert payload["metadata"]["execution"] == "blocked"


def test_sandbox_assignment_run_blocks_string_format_reflection() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={
            "code": (
                "def f():\n"
                "    return 1\n"
                "field = '{0.SystemRandom.random.' + '_' + '_globals' + '_' + "
                "'_[_os].environ}'\n"
                "print(field.format(f))"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["stdout"] == ""
    assert "String field formatting is not allowed" in payload["stderr"]
    assert payload["metadata"]["execution"] == "blocked"


def test_kubernetes_assignment_run_without_kubeconfig_returns_clear_error() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]
    settings_response = client.put(
        "/api/runtime/settings",
        json={
            "backend": "kubernetes",
            "kubeconfig": "",
            "kubernetes_namespace": "agent-runs",
            "sandbox_image": "python:3.12-slim",
        },
    )

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={"code": "print('secret should not echo')"},
    )

    assert settings_response.status_code == 200
    assert settings_response.json()["has_kubeconfig"] is False
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Kubernetes runtime requires kubeconfig before creating runs."
    )
    assert "secret should not echo" not in str(response.json())


def test_kubernetes_assignment_run_with_kubeconfig_prepares_record_without_echoing_secret() -> None:
    client = TestClient(app)
    course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
    assignment_id = course["lessons"][0]["assignment"]["id"]
    client.put(
        "/api/runtime/settings",
        json={
            "backend": "kubernetes",
            "kubeconfig": "apiVersion: v1\nclusters:\n- name: secret-cluster\n",
            "kubernetes_namespace": "agent-runs",
            "sandbox_image": "python:3.12-slim",
        },
    )

    response = client.post(
        f"/api/assignments/{assignment_id}/run",
        json={"code": "print('queued only')"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "kubernetes"
    assert payload["status"] == "queued"
    assert payload["logs"] == [
        "Kubernetes run prepared in namespace agent-runs.",
        "No Job was created by this local preview runner.",
    ]
    assert "secret-cluster" not in str(payload)

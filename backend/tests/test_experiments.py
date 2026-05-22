from __future__ import annotations

import importlib
import json
from collections.abc import Callable, Generator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.services.experiment_runner import ExperimentRunnerError, ExperimentRunnerService


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None]:
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def client_with_artifact_root(
    tmp_path: Path,
    process_runner: Callable[[list[str], Path], Any] | None = None,
    artifact_root: str | None = None,
) -> TestClient:
    def override_settings() -> Settings:
        return Settings(artifact_root=artifact_root or str(tmp_path / "artifacts"))

    app.dependency_overrides[get_settings] = override_settings

    try:
        experiments_route = importlib.import_module("app.api.routes.experiments")
    except ModuleNotFoundError:
        experiments_route = None

    if process_runner is not None and experiments_route is not None:
        dependency = experiments_route.get_experiment_runner_service

        def override_runner() -> Any:
            settings = override_settings()
            service_module = importlib.import_module("app.services.experiment_runner")
            return service_module.ExperimentRunnerService(
                artifact_root=Path(settings.artifact_root),
                process_runner=process_runner,
            )

        app.dependency_overrides[dependency] = override_runner

    return TestClient(app)


def test_minimal_experiment_returns_result_payload(tmp_path: Path) -> None:
    response = client_with_artifact_root(tmp_path).post("/api/experiments/minimal")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "passed"
    assert body["run_id"]
    assert set(body["metrics"]) >= {"initial_loss", "final_loss", "improvement"}
    assert body["logs"]
    artifact_names = {artifact["name"] for artifact in body["artifacts"]}
    assert artifact_names == {"metrics.json", "log.txt"}


def test_minimal_experiment_writes_artifacts_under_configured_root_without_exposing_it(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "artifacts"

    response = client_with_artifact_root(tmp_path).post("/api/experiments/minimal")

    assert response.status_code == 200
    body = response.json()
    run_dir = artifact_root / "experiments" / body["run_id"]
    assert (run_dir / "experiment.py").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "log.txt").is_file()
    for artifact in body["artifacts"]:
        response_path = Path(artifact["path"])
        assert not response_path.is_absolute()
        assert str(tmp_path) not in artifact["path"]
    assert {artifact["path"] for artifact in body["artifacts"]} == {
        f"experiments/{body['run_id']}/metrics.json",
        f"experiments/{body['run_id']}/log.txt",
    }


def test_default_relative_artifact_root_runs_from_temporary_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    service = ExperimentRunnerService(artifact_root=Path("artifacts"))

    result = service.run_minimal_experiment()

    assert result.status == "passed"
    assert (tmp_path / "artifacts" / "experiments" / result.run_id / "metrics.json").is_file()
    assert all(not Path(artifact.path).is_absolute() for artifact in result.artifacts)


def test_relative_artifact_root_rejects_parent_directory_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ExperimentRunnerError, match="Invalid artifact root configuration\\."):
        ExperimentRunnerService(artifact_root=Path("../outside"))

    assert not (tmp_path.parent / "outside").exists()


def test_api_returns_controlled_error_for_invalid_artifact_root_setting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    response = client_with_artifact_root(
        tmp_path,
        artifact_root="../outside-from-settings",
    ).post("/api/experiments/minimal")

    assert response.status_code in {500, 502}
    assert response.json() == {"detail": "Invalid artifact root configuration."}
    assert not (tmp_path.parent / "outside-from-settings").exists()


def test_minimal_experiment_returns_502_when_runner_exits_nonzero(tmp_path: Path) -> None:
    def failing_process_runner(command: list[str], cwd: Path) -> SimpleNamespace:
        return SimpleNamespace(returncode=17, stdout="", stderr="internal failure details" * 100)

    response = client_with_artifact_root(tmp_path, failing_process_runner).post(
        "/api/experiments/minimal",
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Experiment runner failed."}


def test_minimal_experiment_returns_502_for_malformed_metrics(tmp_path: Path) -> None:
    def malformed_metrics_runner(command: list[str], cwd: Path) -> SimpleNamespace:
        (cwd / "metrics.json").write_text("not-json", encoding="utf-8")
        (cwd / "log.txt").write_text("runner completed", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    response = client_with_artifact_root(tmp_path, malformed_metrics_runner).post(
        "/api/experiments/minimal",
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Experiment runner returned invalid artifacts."}


@pytest.mark.parametrize(
    "metrics",
    [
        {"initial_loss": "1.0", "final_loss": 0.1, "improvement": 0.9},
        {"initial_loss": True, "final_loss": 0.1, "improvement": 0.9},
        {"initial_loss": float("nan"), "final_loss": 0.1, "improvement": 0.9},
        {"initial_loss": float("inf"), "final_loss": 0.1, "improvement": 0.9},
        {"initial_loss": 1.0, "final_loss": 0.1},
    ],
)
def test_minimal_experiment_returns_502_for_invalid_metric_values(
    tmp_path: Path,
    metrics: dict[str, Any],
) -> None:
    def invalid_metrics_runner(command: list[str], cwd: Path) -> SimpleNamespace:
        (cwd / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
        (cwd / "log.txt").write_text("runner completed", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    response = client_with_artifact_root(tmp_path, invalid_metrics_runner).post(
        "/api/experiments/minimal",
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Experiment runner returned invalid artifacts."}

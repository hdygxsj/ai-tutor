from __future__ import annotations

import json
import math
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.schemas.experiments import ExperimentArtifact, ExperimentRunResponse


class ProcessResult(Protocol):
    returncode: int
    stdout: str
    stderr: str


ProcessRunner = Callable[[list[str], Path], ProcessResult]


class ExperimentRunnerError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def default_process_runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


class ExperimentRunnerService:
    def __init__(
        self,
        artifact_root: Path,
        process_runner: ProcessRunner = default_process_runner,
    ) -> None:
        self.artifact_root = normalize_artifact_root(artifact_root)
        self.process_runner = process_runner

    def run_minimal_experiment(self) -> ExperimentRunResponse:
        run_id = uuid4().hex
        run_dir = self.artifact_root / "experiments" / run_id
        run_dir.mkdir(parents=True, exist_ok=False)

        script_path = run_dir / "experiment.py"
        script_path.write_text(minimal_experiment_script(), encoding="utf-8")

        result = self.process_runner([sys.executable, str(script_path.resolve())], run_dir)
        if result.returncode != 0:
            raise ExperimentRunnerError("Experiment runner failed.", 502)

        metrics, logs = self._read_artifacts(run_dir)
        return ExperimentRunResponse(
            run_id=run_id,
            status="passed",
            metrics=metrics,
            logs=logs,
            artifacts=[
                ExperimentArtifact(
                    name="metrics.json",
                    path=f"experiments/{run_id}/metrics.json",
                    content_type="application/json",
                ),
                ExperimentArtifact(
                    name="log.txt",
                    path=f"experiments/{run_id}/log.txt",
                    content_type="text/plain",
                ),
            ],
        )

    def _read_artifacts(self, run_dir: Path) -> tuple[dict[str, float], str]:
        metrics_path = run_dir / "metrics.json"
        log_path = run_dir / "log.txt"
        try:
            raw_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            logs = log_path.read_text(encoding="utf-8")
        except (OSError, json.JSONDecodeError) as exc:
            raise ExperimentRunnerError(
                "Experiment runner returned invalid artifacts.",
                502,
            ) from exc

        if not isinstance(raw_metrics, dict) or not logs:
            raise ExperimentRunnerError("Experiment runner returned invalid artifacts.", 502)

        required_metrics = ("initial_loss", "final_loss", "improvement")
        try:
            metrics = {
                name: validate_metric_value(raw_metrics[name])
                for name in required_metrics
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ExperimentRunnerError(
                "Experiment runner returned invalid artifacts.",
                502,
            ) from exc

        return metrics, logs


def validate_metric_value(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError("metric must be a finite number")
    metric = float(value)
    if not math.isfinite(metric):
        raise ValueError("metric must be finite")
    return metric


def normalize_artifact_root(artifact_root: Path) -> Path:
    if not artifact_root.is_absolute() and ".." in artifact_root.parts:
        raise ExperimentRunnerError("Invalid artifact root configuration.", 500)
    return artifact_root.resolve()


def minimal_experiment_script() -> str:
    return '''"""Generated M2.2 minimal experiment runner.

This pure-Python scalar gradient descent script is deterministic. The next
slice can replace the process boundary with Docker/PyTorch execution without
changing the API contract.
"""

import json
from pathlib import Path


def loss(weight: float) -> float:
    target = 3.0
    return (weight - target) ** 2


def main() -> None:
    weight = 0.0
    learning_rate = 0.2
    steps = 20
    initial_loss = loss(weight)
    log_lines = [
        "M2.2 minimal runner: deterministic pure-Python scalar gradient descent.",
        f"initial weight={weight:.6f} loss={initial_loss:.6f}",
    ]

    for step in range(1, steps + 1):
        gradient = 2 * (weight - 3.0)
        weight -= learning_rate * gradient
        if step in {1, 5, 10, 20}:
            log_lines.append(f"step={step} weight={weight:.6f} loss={loss(weight):.6f}")

    final_loss = loss(weight)
    metrics = {
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "improvement": initial_loss - final_loss,
    }

    cwd = Path.cwd()
    (cwd / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (cwd / "log.txt").write_text("\\n".join(log_lines) + "\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
'''

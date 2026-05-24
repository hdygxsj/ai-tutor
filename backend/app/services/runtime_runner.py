import ast
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.tenant import TenantContext
from app.models.learning import (
    Assignment,
    LearningEvent,
    LearningLesson,
    LearningModule,
    RuntimeRun,
)
from app.schemas.runtime import RuntimeRunResponse
from app.services.runtime_settings_service import RuntimeSettingsService


class RuntimeConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class PreparedRun:
    status: str
    stdout: str
    stderr: str
    exit_code: int | None
    test_results: dict[str, Any]
    logs: list[str]
    artifacts: list[dict[str, Any]]
    metadata: dict[str, Any]


class RuntimeRunner:
    backend: str

    def prepare(self, code: str) -> PreparedRun:
        raise NotImplementedError


MAX_CAPTURED_OUTPUT_CHARS = 4000
ALLOWED_IMPORTS: set[str] = set()
DANGEROUS_NAMES = {
    "__builtins__",
    "__import__",
    "breakpoint",
    "classmethod",
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "format",
    "getattr",
    "globals",
    "input",
    "locals",
    "memoryview",
    "object",
    "open",
    "property",
    "setattr",
    "staticmethod",
    "super",
    "type",
    "vars",
}


class SandboxPolicyError(ValueError):
    pass


class SandboxPolicyValidator(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        raise SandboxPolicyError("Import statements are not allowed in sandbox runs.")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise SandboxPolicyError("from-import statements are not allowed in sandbox runs.")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in DANGEROUS_NAMES or node.id.startswith("_"):
            raise SandboxPolicyError(f"Use of {node.id!r} is not allowed in sandbox runs.")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_"):
            raise SandboxPolicyError("Private attribute access is not allowed in sandbox runs.")
        if node.attr in {"format", "format_map"}:
            raise SandboxPolicyError("String field formatting is not allowed in sandbox runs.")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and "__" in node.value:
            raise SandboxPolicyError("Dunder string constants are not allowed in sandbox runs.")


def validate_sandbox_code(code: str) -> None:
    try:
        parsed = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxPolicyError(f"Syntax error: {exc.msg}") from exc
    SandboxPolicyValidator().visit(parsed)


def clip_output(value: str) -> str:
    if len(value) <= MAX_CAPTURED_OUTPUT_CHARS:
        return value
    return f"{value[:MAX_CAPTURED_OUTPUT_CHARS]}\n... output truncated ..."


class SandboxRunner(RuntimeRunner):
    backend = "sandbox"

    def __init__(self, image: str, timeout_seconds: int = 5) -> None:
        self.image = image
        self.timeout_seconds = timeout_seconds

    def prepare(self, code: str) -> PreparedRun:
        try:
            validate_sandbox_code(code)
        except SandboxPolicyError as exc:
            message = str(exc)
            return PreparedRun(
                status="failed",
                stdout="",
                stderr=message,
                exit_code=None,
                test_results={"passed": False, "exit_code": None, "policy_error": message},
                logs=[
                    "Sandbox policy rejected the code before execution.",
                    f"policy_error: {message}",
                ],
                artifacts=[],
                metadata={
                    "execution": "blocked",
                    "image": self.image,
                    "runner_type": "restricted_local_python_subprocess",
                    "shell": False,
                    "timeout_seconds": self.timeout_seconds,
                },
            )
        with tempfile.TemporaryDirectory(prefix="ai-dream-sandbox-") as temporary_directory:
            solution_path = Path(temporary_directory) / "solution.py"
            runner_path = Path(temporary_directory) / "runner.py"
            solution_path.write_text(code, encoding="utf-8")
            runner_path.write_text(RESTRICTED_RUNNER_SCRIPT, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", "-B", str(runner_path)],
                    cwd=temporary_directory,
                    capture_output=True,
                    check=False,
                    env={"PYTHONIOENCODING": "utf-8"},
                    shell=False,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                stdout = clip_output(completed.stdout)
                stderr = clip_output(completed.stderr)
                exit_code = completed.returncode
                status = "completed" if exit_code == 0 else "failed"
            except subprocess.TimeoutExpired as exc:
                stdout = clip_output(exc.stdout if isinstance(exc.stdout, str) else "")
                stderr = clip_output(exc.stderr if isinstance(exc.stderr, str) else "")
                exit_code = None
                status = "failed"
                stderr = f"{stderr}\nTimed out after {self.timeout_seconds}s.".strip()

        test_results = {"passed": exit_code == 0, "exit_code": exit_code}
        logs = [
            f"Sandbox executed Python snippet with image setting {self.image}.",
            f"exit_code: {exit_code}" if exit_code is not None else "exit_code: timeout",
        ]
        if stdout:
            logs.append(f"stdout: {stdout.strip()}")
        if stderr:
            logs.append(f"stderr: {stderr.strip()}")
        return PreparedRun(
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            test_results=test_results,
            logs=logs,
            artifacts=[],
            metadata={
                "execution": "executed",
                "image": self.image,
                "runner_type": "restricted_local_python_subprocess",
                "allowed_imports": sorted(ALLOWED_IMPORTS),
                "shell": False,
                "timeout_seconds": self.timeout_seconds,
            },
        )


RESTRICTED_RUNNER_SCRIPT = """
from pathlib import Path


def _limited_print(*values, sep=" ", end="\\n"):
    print(*values, sep=sep, end=end)


safe_builtins = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "Exception": Exception,
    "False": False,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "print": _limited_print,
    "range": range,
    "round": round,
    "set": set,
    "str": str,
    "sum": sum,
    "SystemExit": SystemExit,
    "tuple": tuple,
    "True": True,
    "ValueError": ValueError,
    "ZeroDivisionError": ZeroDivisionError,
}

source = Path("solution.py").read_text(encoding="utf-8")
safe_globals = {"__builtins__": safe_builtins}
exec(compile(source, "solution.py", "exec"), safe_globals, safe_globals)
"""


class KubernetesRunner(RuntimeRunner):
    backend = "kubernetes"

    def __init__(self, namespace: str, kubeconfig: str | None) -> None:
        self.namespace = namespace
        self.kubeconfig = kubeconfig

    def prepare(self, code: str) -> PreparedRun:
        if not self.kubeconfig or not self.kubeconfig.strip():
            raise RuntimeConfigurationError(
                "Kubernetes runtime requires kubeconfig before creating runs."
            )
        return PreparedRun(
            status="queued",
            stdout="",
            stderr="",
            exit_code=None,
            test_results={"passed": False, "execution": "prepared_only"},
            logs=[
                f"Kubernetes run prepared in namespace {self.namespace}.",
                "No Job was created by this local preview runner.",
            ],
            artifacts=[],
            metadata={
                "execution": "prepared_only",
                "namespace": self.namespace,
                "code_bytes": len(code.encode("utf-8")),
            },
        )


class RuntimeRunService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.db = db
        self.tenant = tenant

    def run_assignment(
        self,
        assignment_id: str,
        code: str,
        session_id: str | None = None,
    ) -> RuntimeRun:
        assignment = self._get_assignment(assignment_id)
        course_id = assignment.lesson.module.plan_id
        configuration = RuntimeSettingsService(self.db, self.tenant).get_runtime_configuration()
        runner = self._build_runner(configuration)
        prepared = runner.prepare(code)
        run = RuntimeRun(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            course_id=course_id,
            assignment_id=assignment.id,
            backend=runner.backend,
            status=prepared.status,
            stdout=prepared.stdout,
            stderr=prepared.stderr,
            exit_code=prepared.exit_code,
            test_results=prepared.test_results,
            logs=prepared.logs,
            artifacts=prepared.artifacts,
            metadata_=prepared.metadata,
        )
        self.db.add_all(
            [
                run,
                LearningEvent(
                    tenant_id=self.tenant.tenant_id,
                    workspace_id=self.tenant.workspace_id,
                    event_type="runtime_run",
                    payload={
                        "course_id": course_id,
                        "assignment_id": assignment.id,
                        "session_id": session_id,
                        "backend": runner.backend,
                        "status": prepared.status,
                        "stdout": prepared.stdout,
                        "stderr": prepared.stderr,
                        "exit_code": prepared.exit_code,
                        "test_results": prepared.test_results,
                        "logs": prepared.logs,
                    },
                ),
            ]
        )
        self.db.commit()
        self.db.refresh(run)
        return run

    def to_response(self, run: RuntimeRun) -> RuntimeRunResponse:
        return RuntimeRunResponse(
            id=run.id,
            course_id=run.course_id,
            assignment_id=run.assignment_id,
            backend=run.backend,  # type: ignore[arg-type]
            status=run.status,
            stdout=run.stdout,
            stderr=run.stderr,
            exit_code=run.exit_code,
            test_results=dict(run.test_results),
            logs=[str(line) for line in run.logs],
            artifacts=list(run.artifacts),
            metadata=dict(run.metadata_),
        )

    def _build_runner(self, configuration: dict[str, Any]) -> RuntimeRunner:
        backend = configuration.get("backend", "sandbox")
        if backend == "kubernetes":
            return KubernetesRunner(
                namespace=str(configuration.get("kubernetes_namespace") or "ai-dream-runs"),
                kubeconfig=configuration.get("kubeconfig"),
            )
        return SandboxRunner(image=str(configuration.get("sandbox_image") or "python:3.12-slim"))

    def _get_assignment(self, assignment_id: str) -> Assignment:
        assignment = self.db.scalar(
            select(Assignment)
            .where(
                Assignment.id == assignment_id,
                Assignment.tenant_id == self.tenant.tenant_id,
                Assignment.workspace_id == self.tenant.workspace_id,
            )
            .options(
                selectinload(Assignment.lesson)
                .selectinload(LearningLesson.module)
                .selectinload(LearningModule.plan)
            )
        )
        if assignment is None:
            raise ValueError("Assignment not found")
        return assignment

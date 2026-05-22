from dataclasses import dataclass
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
    logs: list[str]
    artifacts: list[dict[str, Any]]
    metadata: dict[str, Any]


class RuntimeRunner:
    backend: str

    def prepare(self, code: str) -> PreparedRun:
        raise NotImplementedError


class SandboxRunner(RuntimeRunner):
    backend = "sandbox"

    def __init__(self, image: str) -> None:
        self.image = image

    def prepare(self, code: str) -> PreparedRun:
        preview = code.strip().splitlines()[0][:120] if code.strip() else "<empty>"
        return PreparedRun(
            status="completed",
            logs=[
                f"Sandbox prepared run with image {self.image}.",
                f"Code preview: {preview}",
            ],
            artifacts=[],
            metadata={"execution": "preview_only", "image": self.image},
        )


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

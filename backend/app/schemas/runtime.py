from typing import Literal

from pydantic import BaseModel, Field

RuntimeBackend = Literal["sandbox", "kubernetes"]


class RuntimeSettingsUpdate(BaseModel):
    backend: RuntimeBackend = "sandbox"
    sandbox_image: str = Field(default="python:3.12-slim", min_length=1)
    kubernetes_namespace: str = Field(default="ai-dream-runs", min_length=1)
    kubeconfig: str | None = None


class RuntimeSettingsResponse(BaseModel):
    backend: RuntimeBackend
    sandbox_image: str
    kubernetes_namespace: str
    has_kubeconfig: bool


class RuntimeRunRequest(BaseModel):
    code: str = Field(min_length=1)
    session_id: str | None = None


class RuntimeRunResponse(BaseModel):
    id: str
    course_id: str
    assignment_id: str
    backend: RuntimeBackend
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    test_results: dict = Field(default_factory=dict)
    logs: list[str]
    artifacts: list[dict]
    metadata: dict = Field(default_factory=dict)

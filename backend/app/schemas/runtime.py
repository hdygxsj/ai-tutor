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

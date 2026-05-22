from pydantic import BaseModel


class ExperimentArtifact(BaseModel):
    name: str
    path: str
    content_type: str


class ExperimentRunResponse(BaseModel):
    run_id: str
    status: str
    metrics: dict[str, float]
    logs: str
    artifacts: list[ExperimentArtifact]

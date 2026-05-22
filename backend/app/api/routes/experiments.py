from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.schemas.experiments import ExperimentRunResponse
from app.services.experiment_runner import ExperimentRunnerError, ExperimentRunnerService

router = APIRouter(prefix="/experiments", tags=["experiments"])


def get_experiment_runner_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExperimentRunnerService:
    try:
        return ExperimentRunnerService(artifact_root=Path(settings.artifact_root))
    except ExperimentRunnerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/minimal", response_model=ExperimentRunResponse)
def run_minimal_experiment(
    service: Annotated[ExperimentRunnerService, Depends(get_experiment_runner_service)],
) -> ExperimentRunResponse:
    try:
        return service.run_minimal_experiment()
    except ExperimentRunnerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

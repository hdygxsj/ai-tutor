from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.learning import AssignmentReviewSummary, AssignmentSubmissionRequest
from app.schemas.runtime import RuntimeRunRequest, RuntimeRunResponse
from app.services.grading_service import GradingService
from app.services.runtime_runner import RuntimeConfigurationError, RuntimeRunService

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/{assignment_id}/submit", response_model=AssignmentReviewSummary)
def submit_assignment(
    assignment_id: str,
    request: AssignmentSubmissionRequest,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> AssignmentReviewSummary:
    try:
        review = GradingService(db, tenant).submit_and_grade(assignment_id, request.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Assignment not found") from exc
    return AssignmentReviewSummary.model_validate(review, from_attributes=True)


@router.post("/{assignment_id}/run", response_model=RuntimeRunResponse)
def run_assignment(
    assignment_id: str,
    request: RuntimeRunRequest,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> RuntimeRunResponse:
    service = RuntimeRunService(db, tenant)
    try:
        run = service.run_assignment(
            assignment_id=assignment_id,
            code=request.code,
            session_id=request.session_id,
        )
    except RuntimeConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Assignment not found") from exc
    return service.to_response(run)

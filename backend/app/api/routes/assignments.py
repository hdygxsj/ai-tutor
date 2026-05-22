from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.learning import AssignmentReviewSummary, AssignmentSubmissionRequest
from app.services.grading_service import GradingService

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

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.learning import IntakeRequest, LearningPlanSummary
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/intake", response_model=LearningPlanSummary)
def run_intake(
    request: IntakeRequest,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> LearningPlanSummary:
    return AgentService(db).run_intake(tenant, request)

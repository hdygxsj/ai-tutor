from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.learning import DashboardSummary
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DashboardSummary:
    return DashboardSummary.model_validate(LearningService(db, tenant).get_dashboard())

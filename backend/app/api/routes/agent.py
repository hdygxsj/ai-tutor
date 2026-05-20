from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.api.routes.settings import get_tutor_settings_service
from app.core.tenant import TenantContext
from app.schemas.agent import TutorChatRequest, TutorChatResponse
from app.schemas.learning import IntakeRequest, LearningPlanSummary
from app.services.agent_service import AgentService
from app.services.tutor_provider import TutorProviderError, TutorProviderService
from app.services.tutor_settings_service import TutorSettingsService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_tutor_provider_service(
    settings_service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorProviderService:
    return TutorProviderService(settings_service)


@router.post("/intake", response_model=LearningPlanSummary)
def run_intake(
    request: IntakeRequest,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> LearningPlanSummary:
    return AgentService(db).run_intake(tenant, request)


@router.post("/chat", response_model=TutorChatResponse)
def chat_with_tutor(
    request: TutorChatRequest,
    service: Annotated[TutorProviderService, Depends(get_tutor_provider_service)],
) -> TutorChatResponse:
    try:
        return service.reply(request)
    except TutorProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

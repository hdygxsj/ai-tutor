from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.api.routes.settings import get_tutor_settings_service
from app.core.tenant import TenantContext
from app.schemas.agent import AgentAction, TutorChatRequest, TutorChatResponse
from app.schemas.learning import IntakeRequest, LearningPlanSummary
from app.services.agent_service import AgentService
from app.services.learning_service import AgentSessionService, LearningService
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
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> TutorChatResponse:
    try:
        response = service.reply(request)
    except TutorProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    if request.course_id and request.session_id:
        response.actions = build_course_actions(db, tenant, request.course_id)
        try:
            AgentSessionService(db, tenant).append_chat_turn(
                course_id=request.course_id,
                session_id=request.session_id,
                user_content=request.message,
                assistant_content=response.reply,
                usage=response.usage.model_dump(),
                actions=[action.model_dump() for action in response.actions],
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Agent session not found") from exc
        response.course_id = request.course_id
        response.session_id = request.session_id
    return response


def build_course_actions(
    db: Session,
    tenant: TenantContext,
    course_id: str,
) -> list[AgentAction]:
    try:
        course = LearningService(db, tenant)._get_plan_graph(course_id)
    except ValueError:
        return []

    for module in course.modules:
        for lesson in module.lessons:
            if lesson.assignments:
                assignment = lesson.assignments[0]
                return [
                    AgentAction(
                        type="assignment_ready",
                        label="代码作业已准备",
                        payload={
                            "assignment_id": assignment.id,
                            "title": assignment.title,
                            "prompt": assignment.prompt,
                        },
                    )
                ]
    return []

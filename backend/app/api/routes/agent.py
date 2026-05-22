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
        if response.actions:
            response.reply = build_course_teaching_reply(
                db,
                tenant,
                request.course_id,
                response.reply,
            )
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


def build_course_teaching_reply(
    db: Session,
    tenant: TenantContext,
    course_id: str,
    provider_reply: str,
) -> str:
    try:
        course = LearningService(db, tenant)._get_plan_graph(course_id)
    except ValueError:
        return provider_reply

    for module in course.modules:
        for lesson in module.lessons:
            if lesson.assignments:
                assignment = lesson.assignments[0]
                return (
                    f"{provider_reply}\n\n"
                    f"知识点：{lesson.content} 先把输入、计算图、损失函数和梯度这几个角色串起来，"
                    "再看 requires_grad 如何记录计算、backward 如何把梯度传回叶子张量。\n\n"
                    f"下一步：我已经为你准备了《{assignment.title}》。"
                    "请先按题目要求写出解释或代码，右侧工作区会自动打开，"
                    "你可以在那里运行/提交并获得 Agent 审阅。"
                )
    return provider_reply

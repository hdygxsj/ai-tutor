from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.api.routes.settings import get_tutor_settings_service
from app.core.tenant import TenantContext
from app.models.learning import LearningEvent
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
    course_id = request.course_id
    session_id = request.session_id
    if not course_id:
        course = LearningService(db, tenant).get_active_plan()
        if course is None:
            course = LearningService(db, tenant).create_default_plan(goal=request.message)
        course_id = course.id
    if course_id and not session_id:
        session_id = AgentSessionService(db, tenant).create_session(course_id).id

    if course_id and session_id:
        response.actions = build_course_actions(db, tenant, course_id, request.message)
        response.reply = build_course_teaching_reply(
            db,
            tenant,
            course_id,
            response.reply,
            assignment_ready=bool(response.actions),
        )
        try:
            AgentSessionService(db, tenant).append_chat_turn(
                course_id=course_id,
                session_id=session_id,
                user_content=request.message,
                assistant_content=response.reply,
                usage=response.usage.model_dump(),
                actions=[action.model_dump() for action in response.actions],
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Agent session not found") from exc
        response.course_id = course_id
        response.session_id = session_id
    return response


def build_course_actions(
    db: Session,
    tenant: TenantContext,
    course_id: str,
    message: str,
) -> list[AgentAction]:
    if not should_create_coding_assignment(message):
        return []
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
                            "starter_code": assignment.rubric.get("starter_code", ""),
                            "test_command": assignment.rubric.get("test_command", ""),
                            "tests": assignment.rubric.get("tests", []),
                            "dataset_notes": assignment.rubric.get("dataset_notes", ""),
                        },
                    )
                ]
    return []


def build_course_teaching_reply(
    db: Session,
    tenant: TenantContext,
    course_id: str,
    provider_reply: str,
    assignment_ready: bool,
) -> str:
    try:
        course = LearningService(db, tenant)._get_plan_graph(course_id)
    except ValueError:
        return provider_reply

    for module in course.modules:
        for lesson in module.lessons:
            if lesson.assignments:
                assignment = lesson.assignments[0]
                base_reply = (
                    f"{provider_reply}\n\n"
                    f"知识点：{lesson.content} 先把输入、计算图、损失函数和梯度这几个角色串起来，"
                    "再看 requires_grad 如何记录计算、backward 如何把梯度传回叶子张量。\n\n"
                    "例子：如果 y = x * x，loss = y + 1，那么 backward 会沿计算图把 "
                    "dy/dx 传回 x.grad。\n\n"
                    "检查理解：为什么只有设置 requires_grad=True 的张量才会累计梯度？"
                )
                if not assignment_ready:
                    return f"{base_reply}\n\n下一步：先回答上面的小问题，我确认理解后再进入练习。"
                record_assignment_ready(db, tenant, course_id, assignment.id, assignment.title)
                return (
                    f"{base_reply}\n\n"
                    f"下一步：我已经为你准备了《{assignment.title}》。"
                    "请在右侧工作区完成代码，先运行测试，再提交给 Agent 审阅。"
                )
    return provider_reply


def should_create_coding_assignment(message: str) -> bool:
    coding_keywords = (
        "代码",
        "代码练习",
        "编程",
        "练习",
        "实现",
        "作业",
        "打开ide",
        "打开 ide",
        "coding",
        "code",
        "assignment",
        "exercise",
        "implement",
    )
    lowered = message.lower()
    return any(keyword in lowered for keyword in coding_keywords)


def record_assignment_ready(
    db: Session,
    tenant: TenantContext,
    course_id: str,
    assignment_id: str,
    title: str,
) -> None:
    db.add(
        LearningEvent(
            tenant_id=tenant.tenant_id,
            workspace_id=tenant.workspace_id,
            event_type="assignment_ready",
            payload={"course_id": course_id, "assignment_id": assignment_id, "title": title},
        )
    )

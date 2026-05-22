from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.learning import (
    AgentSessionCreateRequest,
    AgentSessionSummary,
    CourseCreateRequest,
    CourseSummary,
)
from app.services.agent_service import build_plan_summary
from app.services.learning_service import AgentSessionService, LearningService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseSummary])
def list_courses(
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> list[CourseSummary]:
    return [
        CourseSummary.model_validate(build_plan_summary(course).model_dump())
        for course in LearningService(db, tenant).list_courses()
    ]


@router.post("", response_model=CourseSummary)
def create_course(
    request: CourseCreateRequest,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> CourseSummary:
    course = LearningService(db, tenant).create_default_plan(
        goal=request.goal,
        background=request.background,
        weekly_hours=request.weekly_hours,
    )
    return CourseSummary.model_validate(build_plan_summary(course).model_dump())


@router.post("/{course_id}/activate", response_model=CourseSummary)
def activate_course(
    course_id: str,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> CourseSummary:
    try:
        course = LearningService(db, tenant).activate_course(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    return CourseSummary.model_validate(build_plan_summary(course).model_dump())


@router.get("/{course_id}/sessions", response_model=list[AgentSessionSummary])
def list_agent_sessions(
    course_id: str,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> list[AgentSessionSummary]:
    try:
        sessions = AgentSessionService(db, tenant).list_sessions(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    return [AgentSessionSummary.model_validate(session, from_attributes=True) for session in sessions]


@router.post("/{course_id}/sessions", response_model=AgentSessionSummary)
def create_agent_session(
    course_id: str,
    request: AgentSessionCreateRequest,
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> AgentSessionSummary:
    try:
        session = AgentSessionService(db, tenant).create_session(course_id, request.title)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    return AgentSessionSummary.model_validate(session, from_attributes=True)

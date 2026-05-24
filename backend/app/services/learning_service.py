from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.tenant import TenantContext
from app.models.learning import (
    AgentSession,
    Assignment,
    LearnerProfile,
    LearningEvent,
    LearningLesson,
    LearningModule,
    LearningPlan,
    LessonProgress,
)
from app.schemas.learning import CourseTimelineEvent, CourseTimelineResponse


class LearningService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.db = db
        self.tenant = tenant

    def create_default_plan(
        self,
        goal: str | None = None,
        background: str = "",
        weekly_hours: int | None = None,
    ) -> LearningPlan:
        is_intake_plan = goal is not None
        if is_intake_plan:
            self.pause_active_courses()
        plan = LearningPlan(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            title="机器学习教师计划" if is_intake_plan else "PyTorch 自动求导学习计划",
            goal=goal or "掌握 PyTorch 张量与 autograd 基础",
            status="active",
        )
        module = LearningModule(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            title="PyTorch 基础",
            summary="理解张量、梯度追踪和反向传播的最小闭环。",
            position=1,
        )
        lesson = LearningLesson(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            title="张量和 autograd 入门",
            objective="解释 requires_grad 如何启用梯度追踪，并说明 backward 的作用。",
            content=(
                "使用 PyTorch Tensor 表示数据，设置 requires_grad=True 追踪计算图，"
                "再通过 backward() 反向传播得到梯度。"
            ),
            position=1,
        )
        assignment = Assignment(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            title="实现 autograd 的最小训练片段",
            kind="code",
            prompt=(
                "补全一个最小 Python 练习：创建带 requires_grad=True 的变量，"
                "计算 loss，调用 backward，并打印梯度。"
            ),
            rubric={
                "required_concepts": ["requires_grad", "backward"],
                "starter_code": (
                    "x = 2.0\n"
                    "# TODO: 用 requires_grad=True 创建可求导变量\n"
                    "# TODO: 计算一个 loss 并调用 backward()\n"
                    "print('gradient:', 'TODO')\n"
                ),
                "test_command": "python solution.py",
                "tests": [
                    "代码应能用 Python 直接运行。",
                    "stdout 中应打印 gradient。",
                    "提交审阅前至少运行一次沙箱测试。",
                ],
                "dataset_notes": "本练习不需要外部数据集，只使用内置数字样例。",
            },
            status="assigned",
        )
        progress = LessonProgress(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            lesson=lesson,
            status="assignment_ready",
            mastery_score=1 if is_intake_plan else 0,
            next_action="完成 autograd 概念作业" if is_intake_plan else "完成第一份 autograd 练习",
        )
        profile = LearnerProfile(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            display_name="本地学习者",
            goals=[goal] if goal else ["掌握 PyTorch 自动求导基础"],
            background=(
                {"summary": background, "weekly_hours": weekly_hours}
                if is_intake_plan
                else {"level": "beginner"}
            ),
            preferences={"mode": "teacher_loop"},
        )

        plan.modules.append(module)
        module.lessons.append(lesson)
        lesson.assignments.append(assignment)
        lesson.progress_records.append(progress)

        self.db.add_all([profile, plan])
        self.db.flush()
        self.db.add(
            LearningEvent(
                tenant_id=self.tenant.tenant_id,
                workspace_id=self.tenant.workspace_id,
                event_type="plan_created",
                payload={"plan_id": plan.id, "course_id": plan.id, "title": plan.title},
            )
        )
        self.db.add(
            LearningEvent(
                tenant_id=self.tenant.tenant_id,
                workspace_id=self.tenant.workspace_id,
                event_type="assignment_created",
                payload={
                    "course_id": plan.id,
                    "assignment_id": assignment.id,
                    "title": assignment.title,
                },
            )
        )
        self.db.commit()
        return self._get_plan_graph(plan.id)

    def list_courses(self) -> list[LearningPlan]:
        return list(
            self.db.scalars(
                select(LearningPlan)
                .where(
                    LearningPlan.tenant_id == self.tenant.tenant_id,
                    LearningPlan.workspace_id == self.tenant.workspace_id,
                )
                .options(*plan_graph_load_options())
                .order_by(LearningPlan.created_at.desc())
            )
        )

    def activate_course(self, course_id: str) -> LearningPlan:
        course = self._get_plan_graph(course_id)
        self.pause_active_courses(except_course_id=course.id)
        course.status = "active"
        self.db.commit()
        return self._get_plan_graph(course.id)

    def pause_active_courses(self, except_course_id: str | None = None) -> None:
        active_courses = self.db.scalars(
            select(LearningPlan).where(
                LearningPlan.tenant_id == self.tenant.tenant_id,
                LearningPlan.workspace_id == self.tenant.workspace_id,
                LearningPlan.status == "active",
            )
        )
        for course in active_courses:
            if course.id != except_course_id:
                course.status = "paused"

    def get_active_plan(self) -> LearningPlan | None:
        return self.db.scalar(
            select(LearningPlan)
            .where(
                LearningPlan.tenant_id == self.tenant.tenant_id,
                LearningPlan.workspace_id == self.tenant.workspace_id,
                LearningPlan.status == "active",
            )
            .options(*plan_graph_load_options())
            .order_by(LearningPlan.created_at.desc())
        )

    def get_dashboard(self) -> dict[str, Any]:
        active_plan = self.get_active_plan()
        if active_plan is None:
            return {
                "active_plan_title": "",
                "next_action": "创建学习计划",
                "assigned_count": 0,
                "mastery_average": 0,
            }

        assigned_count = self.db.scalar(
            select(func.count())
            .select_from(Assignment)
            .join(Assignment.lesson)
            .join(LearningLesson.module)
            .where(
                Assignment.tenant_id == self.tenant.tenant_id,
                Assignment.workspace_id == self.tenant.workspace_id,
                Assignment.status.in_(["assigned", "needs_revision"]),
                LearningModule.plan_id == active_plan.id,
            )
        )
        mastery_average = self.db.scalar(
            select(func.avg(LessonProgress.mastery_score))
            .select_from(LessonProgress)
            .join(LessonProgress.lesson)
            .join(LearningLesson.module)
            .where(
                LessonProgress.tenant_id == self.tenant.tenant_id,
                LessonProgress.workspace_id == self.tenant.workspace_id,
                LearningModule.plan_id == active_plan.id,
            )
        )
        next_action = self.db.scalar(
            select(LessonProgress.next_action)
            .join(LessonProgress.lesson)
            .join(LearningLesson.module)
            .where(
                LessonProgress.tenant_id == self.tenant.tenant_id,
                LessonProgress.workspace_id == self.tenant.workspace_id,
                LearningModule.plan_id == active_plan.id,
            )
            .order_by(LessonProgress.created_at.asc())
        )

        return {
            "active_plan_title": active_plan.title,
            "next_action": next_action or "继续学习",
            "assigned_count": assigned_count or 0,
            "mastery_average": int(round(mastery_average or 0)),
        }

    def get_course_timeline(self, course_id: str) -> CourseTimelineResponse:
        course = self._get_plan_graph(course_id)
        assignment_ids = {
            assignment.id
            for module in course.modules
            for lesson in module.lessons
            for assignment in lesson.assignments
        }
        session_ids = {session.id for session in course.agent_sessions}
        events = list(
            self.db.scalars(
                select(LearningEvent)
                .where(
                    LearningEvent.tenant_id == self.tenant.tenant_id,
                    LearningEvent.workspace_id == self.tenant.workspace_id,
                )
                .order_by(LearningEvent.created_at.asc())
            )
        )
        timeline_events = [
            self._timeline_event(event)
            for event in events
            if self._event_belongs_to_course(event, course.id, assignment_ids, session_ids)
        ]
        return CourseTimelineResponse(course_id=course.id, events=timeline_events)

    def _get_plan_graph(self, plan_id: str) -> LearningPlan:
        plan = self.db.scalar(
            select(LearningPlan)
            .where(
                LearningPlan.id == plan_id,
                LearningPlan.tenant_id == self.tenant.tenant_id,
                LearningPlan.workspace_id == self.tenant.workspace_id,
            )
            .options(*plan_graph_load_options())
        )
        if plan is None:
            raise ValueError("Learning plan not found")
        return plan

    def _event_belongs_to_course(
        self,
        event: LearningEvent,
        course_id: str,
        assignment_ids: set[str],
        session_ids: set[str],
    ) -> bool:
        payload = event.payload or {}
        return (
            payload.get("course_id") == course_id
            or payload.get("plan_id") == course_id
            or payload.get("assignment_id") in assignment_ids
            or payload.get("session_id") in session_ids
        )

    def _timeline_event(self, event: LearningEvent) -> CourseTimelineEvent:
        return CourseTimelineEvent(
            id=event.id,
            event_type=event.event_type,
            summary=build_event_summary(event.event_type, event.payload or {}),
            created_at=event.created_at.isoformat(),
            payload=event.payload or {},
        )


def plan_graph_load_options() -> tuple[Any, ...]:
    return (
        selectinload(LearningPlan.modules)
        .selectinload(LearningModule.lessons)
        .selectinload(LearningLesson.assignments),
        selectinload(LearningPlan.modules)
        .selectinload(LearningModule.lessons)
        .selectinload(LearningLesson.progress_records),
    )


class AgentSessionService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.db = db
        self.tenant = tenant

    def list_sessions(self, course_id: str) -> list[AgentSession]:
        self._require_course(course_id)
        return list(
            self.db.scalars(
                select(AgentSession)
                .where(
                    AgentSession.tenant_id == self.tenant.tenant_id,
                    AgentSession.workspace_id == self.tenant.workspace_id,
                    AgentSession.course_id == course_id,
                )
                .order_by(AgentSession.updated_at.desc())
            )
        )

    def create_session(self, course_id: str, title: str = "新的 Agent 会话") -> AgentSession:
        self._require_course(course_id)
        session = AgentSession(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            course_id=course_id,
            title=title,
            messages=[],
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, course_id: str, session_id: str) -> AgentSession:
        session = self.db.scalar(
            select(AgentSession).where(
                AgentSession.id == session_id,
                AgentSession.course_id == course_id,
                AgentSession.tenant_id == self.tenant.tenant_id,
                AgentSession.workspace_id == self.tenant.workspace_id,
            )
        )
        if session is None:
            raise ValueError("Agent session not found")
        return session

    def append_chat_turn(
        self,
        course_id: str,
        session_id: str,
        user_content: str,
        assistant_content: str,
        usage: dict[str, Any],
        actions: list[dict[str, Any]] | None = None,
    ) -> AgentSession:
        session = self.get_session(course_id, session_id)
        session.messages = [
            *session.messages,
            {"role": "user", "content": user_content},
            {
                "role": "assistant",
                "content": assistant_content,
                "usage": usage,
                "actions": actions or [],
            },
        ]
        current_usage = session.token_usage or {}
        session.token_usage = {
            "prompt_tokens": int(current_usage.get("prompt_tokens", 0))
            + int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(current_usage.get("completion_tokens", 0))
            + int(usage.get("completion_tokens", 0)),
            "total_tokens": int(current_usage.get("total_tokens", 0))
            + int(usage.get("total_tokens", 0)),
        }
        self.db.add(
            LearningEvent(
                tenant_id=self.tenant.tenant_id,
                workspace_id=self.tenant.workspace_id,
                event_type="agent_session_message",
                payload={
                    "course_id": course_id,
                    "session_id": session_id,
                    "user_message": user_content,
                    "assistant_reply": assistant_content,
                    "actions": actions or [],
                    "usage": usage,
                },
            )
        )
        self.db.commit()
        self.db.refresh(session)
        return session

    def _require_course(self, course_id: str) -> LearningPlan:
        return LearningService(self.db, self.tenant)._get_plan_graph(course_id)


def build_event_summary(event_type: str, payload: dict[str, Any]) -> str:
    if event_type == "plan_created":
        return f"创建课程：{payload.get('title', '未命名课程')}"
    if event_type == "agent_session_message":
        return f"学习者提问：{payload.get('user_message', '')}"
    if event_type == "assignment_graded":
        return f"作业审阅：{payload.get('status', 'unknown')}，得分 {payload.get('score', 0)}"
    if event_type == "submission_reviewed":
        return f"提交审阅：{payload.get('status', 'unknown')}，得分 {payload.get('score', 0)}"
    if event_type == "assignment_created":
        return f"创建作业：{payload.get('title', '未命名作业')}"
    if event_type == "assignment_ready":
        return f"作业就绪：{payload.get('title', '未命名作业')}"
    if event_type == "runtime_run":
        logs = payload.get("logs") or []
        log_preview = logs[-1] if logs else payload.get("status", "")
        return f"运行记录：{payload.get('backend', 'runtime')} {log_preview}"
    return event_type

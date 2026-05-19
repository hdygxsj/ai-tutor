from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.tenant import TenantContext
from app.models.learning import (
    Assignment,
    LearnerProfile,
    LearningEvent,
    LearningLesson,
    LearningModule,
    LearningPlan,
    LessonProgress,
)


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
            title="解释 autograd 的关键步骤",
            kind="concept",
            prompt=(
                "用自己的话解释 requires_grad 和 backward 在 PyTorch autograd "
                "学习闭环中的作用。"
            ),
            rubric={"required_concepts": ["requires_grad", "backward"]},
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
                payload={"plan_id": plan.id, "title": plan.title},
            )
        )
        self.db.commit()
        return self._get_plan_graph(plan.id)

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


def plan_graph_load_options() -> tuple[Any, ...]:
    return (
        selectinload(LearningPlan.modules)
        .selectinload(LearningModule.lessons)
        .selectinload(LearningLesson.assignments),
        selectinload(LearningPlan.modules)
        .selectinload(LearningModule.lessons)
        .selectinload(LearningLesson.progress_records),
    )

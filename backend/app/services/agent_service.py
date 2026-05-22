from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.models.learning import LearningLesson, LearningPlan
from app.schemas.learning import IntakeRequest, LearningPlanSummary, LessonSummary
from app.services.learning_service import LearningService


class AgentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_intake(self, tenant: TenantContext, request: IntakeRequest) -> LearningPlanSummary:
        plan = LearningService(self.db, tenant).create_default_plan(
            goal=request.goal,
            background=request.background,
            weekly_hours=request.weekly_hours,
        )
        return build_plan_summary(plan)


def build_plan_summary(plan: LearningPlan) -> LearningPlanSummary:
    lessons = [
        build_lesson_summary(lesson)
        for module in plan.modules
        for lesson in module.lessons
    ]
    return LearningPlanSummary(
        id=plan.id,
        title=plan.title,
        goal=plan.goal,
        status=plan.status,
        lessons=lessons,
    )


def build_lesson_summary(lesson: LearningLesson) -> LessonSummary:
    progress = lesson.progress_records[0] if lesson.progress_records else None
    assignment = lesson.assignments[0] if lesson.assignments else None
    return LessonSummary(
        id=lesson.id,
        title=lesson.title,
        objective=lesson.objective,
        status=progress.status if progress else "not_started",
        mastery_score=progress.mastery_score if progress else 0,
        next_action=progress.next_action if progress else "开始学习",
        assignment=(
            {
                "id": assignment.id,
                "lesson_id": assignment.lesson_id,
                "title": assignment.title,
                "kind": assignment.kind,
                "prompt": assignment.prompt,
                "status": assignment.status,
            }
            if assignment
            else None
        ),
    )

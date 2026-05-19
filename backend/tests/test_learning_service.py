import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.db.base import Base
from app.models.learning import (
    AgentObservation,
    Assignment,
    AssignmentReview,
    AssignmentSubmission,
    LearnerProfile,
    LearningEvent,
    LearningLesson,
    LearningModule,
    LearningPlan,
    LessonProgress,
    MasteryRecord,
)
from app.services.grading_service import GradingService
from app.services.learning_service import LearningService


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        yield db


def test_create_default_plan_builds_learning_loop_and_dashboard(session: Session) -> None:
    tenant = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    service = LearningService(session, tenant)

    plan = service.create_default_plan()

    assert plan.tenant_id == "tenant-1"
    assert plan.workspace_id == "workspace-1"
    assert plan.status == "active"
    assert plan.modules[0].title == "PyTorch 基础"
    assert plan.modules[0].lessons[0].title == "张量和 autograd 入门"

    lesson = plan.modules[0].lessons[0]
    progress = session.scalar(
        select(LessonProgress).where(
            LessonProgress.tenant_id == tenant.tenant_id,
            LessonProgress.workspace_id == tenant.workspace_id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    assert progress is not None
    assert progress.status == "assignment_ready"
    assert progress.next_action == "完成第一份 autograd 练习"

    assignment = session.scalar(
        select(Assignment).where(
            Assignment.tenant_id == tenant.tenant_id,
            Assignment.workspace_id == tenant.workspace_id,
            Assignment.lesson_id == lesson.id,
        )
    )
    assert assignment is not None
    assert assignment.status == "assigned"
    assert assignment.rubric["required_concepts"] == ["requires_grad", "backward"]

    assert count_rows(session, LearnerProfile) == 1
    created_event = session.scalar(
        select(LearningEvent).where(
            LearningEvent.tenant_id == tenant.tenant_id,
            LearningEvent.workspace_id == tenant.workspace_id,
            LearningEvent.event_type == "plan_created",
        )
    )
    assert created_event is not None
    assert created_event.payload["plan_id"] == plan.id

    dashboard = service.get_dashboard()

    assert dashboard == {
        "active_plan_title": plan.title,
        "next_action": "完成第一份 autograd 练习",
        "assigned_count": 1,
        "mastery_average": 0,
    }


def test_create_default_plan_returns_graph_safe_after_session_detach(session: Session) -> None:
    tenant = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    plan = LearningService(session, tenant).create_default_plan()

    session.expunge_all()

    module = plan.modules[0]
    lesson = module.lessons[0]

    assert module.title == "PyTorch 基础"
    assert lesson.title == "张量和 autograd 入门"
    assert lesson.assignments[0].status == "assigned"
    assert lesson.progress_records[0].status == "assignment_ready"


def test_get_dashboard_scopes_counts_to_current_active_plan(session: Session) -> None:
    tenant = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    create_inactive_plan_with_assignment(
        session=session,
        tenant=tenant,
        next_action="旧计划练习",
        mastery_score=1,
    )
    service = LearningService(session, tenant)
    active_plan = service.create_default_plan()
    active_lesson = active_plan.modules[0].lessons[0]
    active_progress = active_lesson.progress_records[0]
    active_progress.mastery_score = 3
    active_progress.next_action = "当前计划练习"
    session.commit()

    dashboard = service.get_dashboard()

    assert dashboard == {
        "active_plan_title": active_plan.title,
        "next_action": "当前计划练习",
        "assigned_count": 1,
        "mastery_average": 3,
    }


def test_submit_and_grade_passes_answer_and_records_learning_artifacts(
    session: Session,
) -> None:
    tenant = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    learning_service = LearningService(session, tenant)
    plan = learning_service.create_default_plan()
    assignment = plan.modules[0].lessons[0].assignments[0]

    review = GradingService(session, tenant).submit_and_grade(
        assignment_id=assignment.id,
        content="我会设置 tensor.requires_grad=True，然后调用 loss.backward() 计算梯度。",
    )

    assert review.status == "passed"
    assert review.score == 90
    assert review.deterministic_results == {
        "required_concepts": ["requires_grad", "backward"],
        "matched_concepts": ["requires_grad", "backward"],
        "missing_concepts": [],
    }
    assert review.llm_review["verdict"] == "passed"

    session.refresh(assignment)
    assert assignment.status == "completed"
    assert count_rows(session, AssignmentSubmission) == 1
    assert count_rows(session, AssignmentReview) == 1
    assert count_rows(session, MasteryRecord) == 1
    assert count_rows(session, AgentObservation) == 1

    mastery = session.scalar(
        select(MasteryRecord).where(
            MasteryRecord.tenant_id == tenant.tenant_id,
            MasteryRecord.workspace_id == tenant.workspace_id,
        )
    )
    assert mastery is not None
    assert mastery.knowledge_point == "autograd"
    assert mastery.mastery_score == 5

    graded_event = session.scalar(
        select(LearningEvent).where(
            LearningEvent.tenant_id == tenant.tenant_id,
            LearningEvent.workspace_id == tenant.workspace_id,
            LearningEvent.event_type == "assignment_graded",
        )
    )
    assert graded_event is not None
    assert graded_event.payload["status"] == "passed"


def test_submit_and_grade_updates_progress_and_dashboard_after_passing(
    session: Session,
) -> None:
    tenant = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    learning_service = LearningService(session, tenant)
    plan = learning_service.create_default_plan()
    lesson = plan.modules[0].lessons[0]
    assignment = lesson.assignments[0]

    GradingService(session, tenant).submit_and_grade(
        assignment_id=assignment.id,
        content="我会设置 tensor.requires_grad=True，然后调用 loss.backward() 计算梯度。",
    )

    progress = session.scalar(
        select(LessonProgress).where(
            LessonProgress.tenant_id == tenant.tenant_id,
            LessonProgress.workspace_id == tenant.workspace_id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    dashboard = learning_service.get_dashboard()

    assert progress is not None
    assert progress.status == "mastered"
    assert progress.mastery_score == 5
    assert progress.next_action == "进入下一课，或复盘 autograd 关键概念"
    assert dashboard == {
        "active_plan_title": plan.title,
        "next_action": "进入下一课，或复盘 autograd 关键概念",
        "assigned_count": 0,
        "mastery_average": 5,
    }


def test_submit_and_grade_marks_missing_concepts_for_revision(session: Session) -> None:
    tenant = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    learning_service = LearningService(session, tenant)
    plan = learning_service.create_default_plan()
    assignment = plan.modules[0].lessons[0].assignments[0]

    review = GradingService(session, tenant).submit_and_grade(
        assignment_id=assignment.id,
        content="张量可以保存数字并参与模型计算。",
    )

    assert review.status == "needs_revision"
    assert review.score == 45
    assert review.deterministic_results["missing_concepts"] == ["requires_grad", "backward"]
    assert review.llm_review["verdict"] == "needs_revision"

    session.refresh(assignment)
    assert assignment.status == "needs_revision"

    progress = plan.modules[0].lessons[0].progress_records[0]
    session.refresh(progress)
    assert progress.status == "needs_revision"
    assert progress.mastery_score == 2
    assert progress.next_action == "重做作业，并复习 autograd 的 requires_grad 与 backward"

    dashboard = learning_service.get_dashboard()
    assert dashboard == {
        "active_plan_title": plan.title,
        "next_action": "重做作业，并复习 autograd 的 requires_grad 与 backward",
        "assigned_count": 1,
        "mastery_average": 2,
    }


def test_submit_and_grade_rejects_cross_tenant_assignment_id(session: Session) -> None:
    tenant_1 = TenantContext(tenant_id="tenant-1", workspace_id="workspace-1")
    tenant_2 = TenantContext(tenant_id="tenant-2", workspace_id="workspace-1")
    plan = LearningService(session, tenant_1).create_default_plan()
    assignment = plan.modules[0].lessons[0].assignments[0]

    with pytest.raises(ValueError, match="Assignment not found"):
        GradingService(session, tenant_2).submit_and_grade(
            assignment_id=assignment.id,
            content="requires_grad and backward",
        )

    assert count_rows(session, AssignmentSubmission) == 0
    assert count_rows(session, AssignmentReview) == 0


def count_rows(session: Session, model: type[Base]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def create_inactive_plan_with_assignment(
    session: Session,
    tenant: TenantContext,
    next_action: str,
    mastery_score: int,
) -> None:
    plan = LearningPlan(
        tenant_id=tenant.tenant_id,
        workspace_id=tenant.workspace_id,
        title="旧 PyTorch 计划",
        goal="旧目标",
        status="archived",
    )
    module = LearningModule(
        tenant_id=tenant.tenant_id,
        workspace_id=tenant.workspace_id,
        title="旧模块",
        summary="旧计划模块",
        position=1,
    )
    lesson = LearningLesson(
        tenant_id=tenant.tenant_id,
        workspace_id=tenant.workspace_id,
        title="旧课程",
        objective="旧目标",
        content="旧内容",
        position=1,
    )
    progress = LessonProgress(
        tenant_id=tenant.tenant_id,
        workspace_id=tenant.workspace_id,
        lesson=lesson,
        status="assignment_ready",
        mastery_score=mastery_score,
        next_action=next_action,
    )
    assignment = Assignment(
        tenant_id=tenant.tenant_id,
        workspace_id=tenant.workspace_id,
        lesson=lesson,
        title="旧作业",
        kind="concept",
        prompt="旧作业",
        rubric={"required_concepts": ["old"]},
        status="assigned",
    )

    plan.modules.append(module)
    module.lessons.append(lesson)
    lesson.progress_records.append(progress)
    lesson.assignments.append(assignment)
    session.add(plan)
    session.commit()

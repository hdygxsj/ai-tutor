import pytest
from pydantic import ValidationError
from sqlalchemy import UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.schemas.learning import IntakeRequest


def test_learning_metadata_registers_required_tables_and_constraints() -> None:
    expected_tables = {
        "learner_profiles",
        "learning_plans",
        "learning_modules",
        "learning_lessons",
        "lesson_progress",
        "assignments",
        "assignment_submissions",
        "assignment_reviews",
        "mastery_records",
        "learning_events",
        "agent_observations",
    }

    assert expected_tables.issubset(Base.metadata.tables)

    lesson_progress = Base.metadata.tables["lesson_progress"]
    constraint_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in lesson_progress.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("tenant_id", "workspace_id", "lesson_id") in constraint_columns


def test_learning_plan_relationship_graph_supports_plan_module_lessons() -> None:
    from app.models.learning import LearningLesson, LearningModule, LearningPlan

    plan = LearningPlan(title="Python foundations", goal="Learn Python")
    module = LearningModule(title="Basics", summary="Core Python concepts", position=1)
    lesson = LearningLesson(
        title="Variables",
        objective="Understand variables",
        content="Variables store values for later use.",
        position=1,
    )

    plan.modules.append(module)
    module.lessons.append(lesson)

    assert plan.modules[0].plan is plan
    assert plan.modules[0].lessons[0].module is module


def test_learning_plan_delete_cascades_contained_learning_loop_rows() -> None:
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

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        profile = LearnerProfile(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            display_name="Ada",
            goals=["Learn AI"],
            background={"experience": "Python"},
            preferences={"pace": "steady"},
        )
        plan = LearningPlan(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            title="AI foundations",
            goal="Learn AI",
        )
        module = LearningModule(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            title="Basics",
            summary="Foundational vector concepts.",
            position=1,
        )
        lesson = LearningLesson(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            title="Vectors",
            objective="Understand vectors",
            content="Vectors represent ordered numeric values.",
            position=1,
        )
        progress = LessonProgress(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            lesson=lesson,
            status="in_progress",
            mastery_score=2,
            next_action="Continue vector practice",
        )
        assignment = Assignment(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            lesson=lesson,
            title="Vector practice",
            kind="practice",
            prompt="Solve a vector exercise.",
            rubric={"requires": ["magnitude"]},
            status="assigned",
        )
        submission = AssignmentSubmission(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            assignment=assignment,
            content="My answer",
            evidence={"attempt": 1},
        )
        review = AssignmentReview(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            submission=submission,
            status="reviewed",
            score=80,
            deterministic_results={"contains_keywords": True},
            llm_review={"summary": "Good start"},
            feedback="Shows basic vector understanding.",
        )
        mastery = MasteryRecord(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            knowledge_point="vectors",
            mastery_score=3,
            evidence={"source": "diagnostic"},
        )
        event_row = LearningEvent(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            event_type="lesson_started",
            payload={"lesson_title": "Vectors"},
        )
        observation = AgentObservation(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            observation_type="engagement",
            summary="Ready to learn",
            evidence={"signal": "active"},
        )

        plan.modules.append(module)
        module.lessons.append(lesson)
        assignment.submissions.append(submission)
        submission.reviews.append(review)
        session.add_all([profile, plan, progress, assignment, mastery, event_row, observation])
        session.commit()

        assert profile.goals == ["Learn AI"]
        assert profile.background == {"experience": "Python"}
        assert profile.preferences == {"pace": "steady"}
        assert progress.status == "in_progress"
        assert progress.mastery_score == 2
        assert progress.next_action == "Continue vector practice"
        assert assignment.kind == "practice"
        assert assignment.prompt == "Solve a vector exercise."
        assert assignment.rubric == {"requires": ["magnitude"]}
        assert assignment.status == "assigned"
        assert submission.evidence == {"attempt": 1}
        assert review.deterministic_results == {"contains_keywords": True}
        assert review.llm_review == {"summary": "Good start"}
        assert review.feedback == "Shows basic vector understanding."
        assert mastery.knowledge_point == "vectors"
        assert mastery.evidence == {"source": "diagnostic"}
        assert event_row.payload == {"lesson_title": "Vectors"}
        assert observation.evidence == {"signal": "active"}

        session.delete(plan)
        session.commit()

        for model in (
            LearningPlan,
            LearningModule,
            LearningLesson,
            LessonProgress,
            Assignment,
            AssignmentSubmission,
            AssignmentReview,
        ):
            assert count_rows(session, model) == 0

        assert count_rows(session, LearnerProfile) == 1
        assert count_rows(session, MasteryRecord) == 1
        assert count_rows(session, LearningEvent) == 1
        assert count_rows(session, AgentObservation) == 1


def test_learning_plan_timestamps_are_stored_as_utc_naive_datetimes() -> None:
    from app.models.learning import LearningPlan

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        plan = LearningPlan(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            title="AI foundations",
            goal="Learn AI",
        )

        session.add(plan)
        session.flush()

        assert plan.created_at is not None
        assert plan.updated_at is not None
        assert plan.created_at.tzinfo is None
        assert plan.updated_at.tzinfo is None


def count_rows(session: Session, model: type[Base]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_intake_request_validates_goal_and_weekly_hours() -> None:
    request = IntakeRequest(goal="Learn AI", weekly_hours=8)

    assert request.background == ""
    assert request.weekly_hours == 8

    with pytest.raises(ValidationError):
        IntakeRequest(goal="AI")

    with pytest.raises(ValidationError):
        IntakeRequest(goal="Learn AI", weekly_hours=0)

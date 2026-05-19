import pytest
from pydantic import ValidationError
from sqlalchemy import Integer, UniqueConstraint

from app.db.base import Base
from app.schemas.learning import DashboardSummary, IntakeRequest, LessonSummary


def test_learning_metadata_contains_core_tables_and_tenant_fields() -> None:
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

    for table_name in expected_tables:
        table = Base.metadata.tables[table_name]
        assert table.c.tenant_id.type.length == 64
        assert table.c.workspace_id.type.length == 64
        assert table.c.tenant_id.index is True
        assert table.c.workspace_id.index is True


def test_lesson_progress_is_unique_per_tenant_workspace_lesson() -> None:
    lesson_progress = Base.metadata.tables["lesson_progress"]
    unique_constraints = {
        tuple(column.name for column in constraint.columns)
        for constraint in lesson_progress.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("tenant_id", "workspace_id", "lesson_id") in unique_constraints


def test_mastery_scores_are_integer_columns() -> None:
    lesson_progress = Base.metadata.tables["lesson_progress"]
    mastery_records = Base.metadata.tables["mastery_records"]

    assert isinstance(lesson_progress.c.mastery_score.type, Integer)
    assert isinstance(mastery_records.c.mastery_score.type, Integer)


def test_learning_schemas_validate_intake_and_accept_status_strings() -> None:
    request = IntakeRequest(goal="Learn AI", weekly_hours=8)

    assert request.background == ""
    assert request.weekly_hours == 8

    with pytest.raises(ValidationError):
        IntakeRequest(goal="AI")

    with pytest.raises(ValidationError):
        IntakeRequest(goal="Learn AI", weekly_hours=81)

    lesson = LessonSummary(
        id="lesson-1",
        title="Vectors",
        objective="Understand vector basics",
        status="ready_for_review",
        mastery_score=3,
        next_action="Submit practice",
    )
    dashboard = DashboardSummary(
        active_plan_title="AI foundations",
        next_action="Submit practice",
        assigned_count=1,
        mastery_average=3,
    )

    assert lesson.status == "ready_for_review"
    assert lesson.mastery_score == 3
    assert dashboard.mastery_average == 3

    with pytest.raises(ValidationError):
        LessonSummary(
            id="lesson-1",
            title="Vectors",
            objective="Understand vector basics",
            status="ready_for_review",
            mastery_score=0.5,
            next_action="Submit practice",
        )

    with pytest.raises(ValidationError):
        DashboardSummary(
            active_plan_title="AI foundations",
            next_action="Submit practice",
            assigned_count=1,
            mastery_average=0.5,
        )

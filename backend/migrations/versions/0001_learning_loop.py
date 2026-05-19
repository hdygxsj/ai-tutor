"""create learning loop tables

Revision ID: 0001_learning_loop
Revises:
Create Date: 2026-05-19 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_learning_loop"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LEARNING_TABLES = [
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
]


def tenant_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def create_tenant_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"])
    op.create_index(f"ix_{table_name}_workspace_id", table_name, ["workspace_id"])


def drop_tenant_indexes(table_name: str) -> None:
    op.drop_index(f"ix_{table_name}_workspace_id", table_name=table_name)
    op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "learner_profiles",
        *tenant_columns(),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("background", sa.JSON(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "learning_plans",
        *tenant_columns(),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "learning_modules",
        *tenant_columns(),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["learning_plans.id"],
            name="fk_learning_modules_plan_id_learning_plans",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "learning_lessons",
        *tenant_columns(),
        sa.Column("module_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["learning_modules.id"],
            name="fk_learning_lessons_module_id_learning_modules",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lesson_progress",
        *tenant_columns(),
        sa.Column("lesson_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("mastery_score", sa.Integer(), nullable=False),
        sa.Column("next_action", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["learning_lessons.id"],
            name="fk_lesson_progress_lesson_id_learning_lessons",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workspace_id",
            "lesson_id",
            name="uq_lesson_progress_tenant_workspace_lesson",
        ),
    )

    op.create_table(
        "assignments",
        *tenant_columns(),
        sa.Column("lesson_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rubric", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["learning_lessons.id"],
            name="fk_assignments_lesson_id_learning_lessons",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assignment_submissions",
        *tenant_columns(),
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.id"],
            name="fk_assignment_submissions_assignment_id_assignments",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assignment_reviews",
        *tenant_columns(),
        sa.Column("submission_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("deterministic_results", sa.JSON(), nullable=False),
        sa.Column("llm_review", sa.JSON(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["assignment_submissions.id"],
            name="fk_assignment_reviews_submission_id_assignment_submissions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "mastery_records",
        *tenant_columns(),
        sa.Column("knowledge_point", sa.String(length=255), nullable=False),
        sa.Column("mastery_score", sa.Integer(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "learning_events",
        *tenant_columns(),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "agent_observations",
        *tenant_columns(),
        sa.Column("observation_type", sa.String(length=128), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    for table_name in LEARNING_TABLES:
        create_tenant_indexes(table_name)


def downgrade() -> None:
    for table_name in reversed(LEARNING_TABLES):
        drop_tenant_indexes(table_name)
        op.drop_table(table_name)

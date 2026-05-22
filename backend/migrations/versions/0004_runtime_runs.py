"""add runtime run records

Revision ID: 0004_runtime_runs
Revises: 0003_workspace_settings
Create Date: 2026-05-23 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_runtime_runs"
down_revision: str | None = "0003_workspace_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runtime_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("backend", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("logs", sa.JSON(), nullable=False),
        sa.Column("artifacts", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["learning_plans.id"],
            name="fk_runtime_runs_course_id_learning_plans",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.id"],
            name="fk_runtime_runs_assignment_id_assignments",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_runtime_runs_tenant_id", "runtime_runs", ["tenant_id"])
    op.create_index("ix_runtime_runs_workspace_id", "runtime_runs", ["workspace_id"])
    op.create_index("ix_runtime_runs_course_id", "runtime_runs", ["course_id"])
    op.create_index("ix_runtime_runs_assignment_id", "runtime_runs", ["assignment_id"])


def downgrade() -> None:
    op.drop_index("ix_runtime_runs_assignment_id", table_name="runtime_runs")
    op.drop_index("ix_runtime_runs_course_id", table_name="runtime_runs")
    op.drop_index("ix_runtime_runs_workspace_id", table_name="runtime_runs")
    op.drop_index("ix_runtime_runs_tenant_id", table_name="runtime_runs")
    op.drop_table("runtime_runs")

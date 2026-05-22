"""add persisted agent sessions

Revision ID: 0002_agent_sessions
Revises: 0001_learning_loop
Create Date: 2026-05-22 23:05:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_agent_sessions"
down_revision: str | None = "0001_learning_loop"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("messages", sa.JSON(), nullable=False),
        sa.Column("token_usage", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["learning_plans.id"],
            name="fk_agent_sessions_course_id_learning_plans",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_sessions_tenant_id", "agent_sessions", ["tenant_id"])
    op.create_index("ix_agent_sessions_workspace_id", "agent_sessions", ["workspace_id"])
    op.create_index("ix_agent_sessions_course_id", "agent_sessions", ["course_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_sessions_course_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_workspace_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_tenant_id", table_name="agent_sessions")
    op.drop_table("agent_sessions")

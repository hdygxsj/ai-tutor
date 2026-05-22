"""add workspace settings table

Revision ID: 0003_workspace_settings
Revises: 0002_agent_sessions
Create Date: 2026-05-22 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_workspace_settings"
down_revision: str | None = "0002_agent_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workspace_id",
            "key",
            name="uq_workspace_settings_scope_key",
        ),
    )
    op.create_index("ix_workspace_settings_tenant_id", "workspace_settings", ["tenant_id"])
    op.create_index("ix_workspace_settings_workspace_id", "workspace_settings", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_workspace_settings_workspace_id", table_name="workspace_settings")
    op.drop_index("ix_workspace_settings_tenant_id", table_name="workspace_settings")
    op.drop_table("workspace_settings")

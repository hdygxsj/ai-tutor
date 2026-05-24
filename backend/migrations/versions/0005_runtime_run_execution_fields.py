"""add runtime run execution fields

Revision ID: 0005_runtime_run_execution_fields
Revises: 0004_runtime_runs
Create Date: 2026-05-23 00:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_runtime_run_execution_fields"
down_revision: str | None = "0004_runtime_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runtime_runs", sa.Column("stdout", sa.Text(), nullable=False, server_default=""))
    op.add_column("runtime_runs", sa.Column("stderr", sa.Text(), nullable=False, server_default=""))
    op.add_column("runtime_runs", sa.Column("exit_code", sa.Integer(), nullable=True))
    op.add_column(
        "runtime_runs",
        sa.Column("test_results", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.alter_column("runtime_runs", "stdout", server_default=None)
    op.alter_column("runtime_runs", "stderr", server_default=None)
    op.alter_column("runtime_runs", "test_results", server_default=None)


def downgrade() -> None:
    op.drop_column("runtime_runs", "test_results")
    op.drop_column("runtime_runs", "exit_code")
    op.drop_column("runtime_runs", "stderr")
    op.drop_column("runtime_runs", "stdout")

"""validations 表 (科学验证, Sprint 5)

Revision ID: 0006_validations
Revises: 0005_backtests
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_validations"
down_revision: Union[str, None] = "0005_backtests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "validations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("cost_config", sa.JSON(), nullable=False),
        sa.Column("oos_ratio", sa.Float(), server_default="0.3", nullable=False),
        sa.Column("n_splits", sa.Integer(), server_default="4", nullable=False),
        sa.Column("oos", sa.JSON(), nullable=True),
        sa.Column("walk_forward", sa.JSON(), nullable=True),
        sa.Column("sensitivity", sa.JSON(), nullable=True),
        sa.Column("robustness", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["data_snapshots.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_validations_owner_id"), "validations", ["owner_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_validations_owner_id"), table_name="validations")
    op.drop_table("validations")

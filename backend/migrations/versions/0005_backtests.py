"""market_datasets / data_snapshots / backtests (回测系统, Sprint 4)

Revision ID: 0005_backtests
Revises: 0004_factors
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_backtests"
down_revision: Union[str, None] = "0004_factors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), server_default="1d", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rows", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "timeframe", name="uq_dataset_symbol_tf"),
    )
    op.create_index(op.f("ix_market_datasets_symbol"), "market_datasets", ["symbol"])

    op.create_table(
        "data_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), server_default="1d", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rows", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_snapshots_symbol"), "data_snapshots", ["symbol"])
    op.create_index(op.f("ix_data_snapshots_content_hash"), "data_snapshots", ["content_hash"])

    op.create_table(
        "backtests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("cost_config", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("equity_curve", sa.JSON(), nullable=True),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["data_snapshots.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtests_owner_id"), "backtests", ["owner_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_backtests_owner_id"), table_name="backtests")
    op.drop_table("backtests")
    op.drop_index(op.f("ix_data_snapshots_content_hash"), table_name="data_snapshots")
    op.drop_index(op.f("ix_data_snapshots_symbol"), table_name="data_snapshots")
    op.drop_table("data_snapshots")
    op.drop_index(op.f("ix_market_datasets_symbol"), table_name="market_datasets")
    op.drop_table("market_datasets")

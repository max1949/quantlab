"""Paper tracking snapshots + optional python factor kind extension.

Revision ID: 0013_paper_tracking
Revises: 0012_membership
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_paper_tracking"
down_revision: Union[str, None] = "0012_membership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timeframe", sa.String(length=8), server_default="1d", nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("bars", sa.Integer(), nullable=False),
        sa.Column("nav_end", sa.Float(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("equity_tail", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("factor_id", "as_of_date", name="uq_paper_factor_date"),
    )
    op.create_index("ix_paper_snapshots_factor_id", "paper_snapshots", ["factor_id"])
    op.create_index("ix_paper_snapshots_owner_id", "paper_snapshots", ["owner_id"])
    op.create_index("ix_paper_snapshots_as_of_date", "paper_snapshots", ["as_of_date"])


def downgrade() -> None:
    op.drop_index("ix_paper_snapshots_as_of_date", table_name="paper_snapshots")
    op.drop_index("ix_paper_snapshots_owner_id", table_name="paper_snapshots")
    op.drop_index("ix_paper_snapshots_factor_id", table_name="paper_snapshots")
    op.drop_table("paper_snapshots")

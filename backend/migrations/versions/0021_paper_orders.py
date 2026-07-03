"""paper_orders: institutional paper execution scaffold.

Revision ID: 0021_paper_orders
Revises: 0020_org_subscriptions
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_paper_orders"
down_revision: Union[str, None] = "0020_org_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("notional_cny", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="filled"),
        sa.Column("signal_value", sa.Numeric(12, 6), nullable=True),
        sa.Column("regime", sa.String(length=8), nullable=True),
        sa.Column("regime_fit_score", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=200), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_paper_orders_user_id"), "paper_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_paper_orders_factor_id"), "paper_orders", ["factor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_paper_orders_factor_id"), table_name="paper_orders")
    op.drop_index(op.f("ix_paper_orders_user_id"), table_name="paper_orders")
    op.drop_table("paper_orders")

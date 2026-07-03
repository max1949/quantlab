"""execution channels on paper_orders.

Revision ID: 0022_execution_channels
Revises: 0021_paper_orders
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_execution_channels"
down_revision: Union[str, None] = "0021_paper_orders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "paper_orders",
        sa.Column("channel", sa.String(length=16), nullable=False, server_default="paper"),
    )
    op.add_column(
        "paper_orders",
        sa.Column("external_ref", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "paper_orders",
        sa.Column("risk_verdict", sa.String(length=16), nullable=False, server_default="passed"),
    )
    op.add_column(
        "paper_orders",
        sa.Column("risk_detail", sa.String(length=300), nullable=False, server_default=""),
    )
    op.add_column(
        "paper_orders",
        sa.Column("routed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("paper_orders", "routed_at")
    op.drop_column("paper_orders", "risk_detail")
    op.drop_column("paper_orders", "risk_verdict")
    op.drop_column("paper_orders", "external_ref")
    op.drop_column("paper_orders", "channel")

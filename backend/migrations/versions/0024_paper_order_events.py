"""paper order status event log.

Revision ID: 0024_paper_order_events
Revises: 0023_execution_webhook_org_sso
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024_paper_order_events"
down_revision: Union[str, None] = "0023_execution_webhook_org_sso"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_order_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=16), nullable=True),
        sa.Column("to_status", sa.String(length=16), nullable=True),
        sa.Column("gateway_status", sa.String(length=32), nullable=True),
        sa.Column("detail", sa.String(length=500), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["paper_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_order_events_order_id", "paper_order_events", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_paper_order_events_order_id", table_name="paper_order_events")
    op.drop_table("paper_order_events")

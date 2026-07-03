"""institutional billing ledger.

Revision ID: 0025_billing_ledger
Revises: 0024_paper_order_events
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025_billing_ledger"
down_revision: Union[str, None] = "0024_paper_order_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_ledger",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("plan_code", sa.String(length=40), nullable=False),
        sa.Column("plan_name", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seats", sa.Integer(), nullable=True),
        sa.Column("amount_cny", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="redeem"),
        sa.Column("stripe_session_id", sa.String(length=120), nullable=True),
        sa.Column("subscription_ref", sa.Uuid(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detail", sa.String(length=300), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["research_orgs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_ledger_org_id", "billing_ledger", ["org_id"])
    op.create_index("ix_billing_ledger_user_id", "billing_ledger", ["user_id"])
    op.create_index("ix_billing_ledger_created_at", "billing_ledger", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_billing_ledger_created_at", table_name="billing_ledger")
    op.drop_index("ix_billing_ledger_user_id", table_name="billing_ledger")
    op.drop_index("ix_billing_ledger_org_id", table_name="billing_ledger")
    op.drop_table("billing_ledger")

"""org_subscriptions: institutional team billing.

Revision ID: 0020_org_subscriptions
Revises: 0019_org_invites
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_org_subscriptions"
down_revision: Union[str, None] = "0019_org_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "org_subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("plan_code", sa.String(length=40), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("seats", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="redeem"),
        sa.Column("stripe_session_id", sa.String(length=120), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["research_orgs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_org_subscriptions_org_id"), "org_subscriptions", ["org_id"], unique=False)

    op.add_column(
        "redeem_codes",
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="personal"),
    )
    op.add_column(
        "redeem_codes",
        sa.Column("seats", sa.Integer(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("stripe_session_id", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "stripe_session_id")
    op.drop_column("redeem_codes", "seats")
    op.drop_column("redeem_codes", "kind")
    op.drop_index(op.f("ix_org_subscriptions_org_id"), table_name="org_subscriptions")
    op.drop_table("org_subscriptions")

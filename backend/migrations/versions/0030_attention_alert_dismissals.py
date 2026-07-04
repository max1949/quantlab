"""attention alert dismissals with cooldown.

Revision ID: 0030_attention_alert_dismissals
Revises: 0029_org_billing_profile
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0030_attention_alert_dismissals"
down_revision: Union[str, None] = "0029_org_billing_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attention_alert_dismissals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("alert_key", sa.String(length=128), nullable=False),
        sa.Column(
            "dismissed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "alert_key", name="uq_attention_alert_dismiss"),
    )
    op.create_index(
        op.f("ix_attention_alert_dismissals_user_id"),
        "attention_alert_dismissals",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_attention_alert_dismissals_user_id"),
        table_name="attention_alert_dismissals",
    )
    op.drop_table("attention_alert_dismissals")

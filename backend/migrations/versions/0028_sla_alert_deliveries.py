"""sla alert delivery audit log.

Revision ID: 0028_sla_alert_deliveries
Revises: 0027_org_alert_webhook_secret
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0028_sla_alert_deliveries"
down_revision: Union[str, None] = "0027_org_alert_webhook_secret"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sla_alert_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("trigger", sa.String(length=16), nullable=False, server_default="scheduled"),
        sa.Column("alert_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_reason", sa.String(length=64), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("signed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("detail", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("retry_of_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["research_orgs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retry_of_id"], ["sla_alert_deliveries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sla_alert_deliveries_scope", "sla_alert_deliveries", ["scope"])
    op.create_index("ix_sla_alert_deliveries_org_id", "sla_alert_deliveries", ["org_id"])
    op.create_index("ix_sla_alert_deliveries_status", "sla_alert_deliveries", ["status"])
    op.create_index("ix_sla_alert_deliveries_created_at", "sla_alert_deliveries", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_sla_alert_deliveries_created_at", table_name="sla_alert_deliveries")
    op.drop_index("ix_sla_alert_deliveries_status", table_name="sla_alert_deliveries")
    op.drop_index("ix_sla_alert_deliveries_org_id", table_name="sla_alert_deliveries")
    op.drop_index("ix_sla_alert_deliveries_scope", table_name="sla_alert_deliveries")
    op.drop_table("sla_alert_deliveries")

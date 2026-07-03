"""org alert webhook url.

Revision ID: 0026_org_alert_webhook
Revises: 0025_billing_ledger
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026_org_alert_webhook"
down_revision: Union[str, None] = "0025_billing_ledger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "research_orgs",
        sa.Column("alert_webhook_url", sa.String(length=500), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("research_orgs", "alert_webhook_url")

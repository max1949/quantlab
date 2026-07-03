"""org alert webhook signing secret.

Revision ID: 0027_org_alert_webhook_secret
Revises: 0026_org_alert_webhook
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027_org_alert_webhook_secret"
down_revision: Union[str, None] = "0026_org_alert_webhook"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "research_orgs",
        sa.Column("alert_webhook_secret", sa.String(length=200), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("research_orgs", "alert_webhook_secret")

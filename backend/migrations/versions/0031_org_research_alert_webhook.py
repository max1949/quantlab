"""org research alert webhook columns

Revision ID: 0031_org_research_alert_webhook
Revises: 0030_attention_alert_dismissals
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0031_org_research_alert_webhook"
down_revision: Union[str, None] = "0030_attention_alert_dismissals"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.add_column(
        "research_orgs",
        sa.Column("research_alert_webhook_url", sa.String(length=500), nullable=False, server_default=""),
    )
    op.add_column(
        "research_orgs",
        sa.Column("research_alert_webhook_secret", sa.String(length=200), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("research_orgs", "research_alert_webhook_secret")
    op.drop_column("research_orgs", "research_alert_webhook_url")

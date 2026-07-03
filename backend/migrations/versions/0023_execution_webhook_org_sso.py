"""execution webhook fields + org SSO domains.

Revision ID: 0023_execution_webhook_org_sso
Revises: 0022_execution_channels
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_execution_webhook_org_sso"
down_revision: Union[str, None] = "0022_execution_channels"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "paper_orders",
        sa.Column("gateway_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "paper_orders",
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "research_orgs",
        sa.Column("sso_email_domains", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("research_orgs", "sso_email_domains")
    op.drop_column("paper_orders", "filled_at")
    op.drop_column("paper_orders", "gateway_status")

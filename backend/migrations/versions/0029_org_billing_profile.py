"""org billing profile for invoice PDF headers.

Revision ID: 0029_org_billing_profile
Revises: 0028_sla_alert_deliveries
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029_org_billing_profile"
down_revision: Union[str, None] = "0028_sla_alert_deliveries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "research_orgs",
        sa.Column("billing_company_name", sa.String(length=200), nullable=False, server_default=""),
    )
    op.add_column(
        "research_orgs",
        sa.Column("billing_tax_id", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "research_orgs",
        sa.Column("billing_address", sa.String(length=300), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("research_orgs", "billing_address")
    op.drop_column("research_orgs", "billing_tax_id")
    op.drop_column("research_orgs", "billing_company_name")

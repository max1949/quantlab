"""Make generated reports private until publish/share.

Revision ID: 0015_private_reports_by_default
Revises: 0014_perf_indexes
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_private_reports_by_default"
down_revision: Union[str, None] = "0014_perf_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "research_reports",
        "is_public",
        server_default=sa.text("false"),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.execute(
        """
        UPDATE research_reports AS rr
        SET is_public = false
        WHERE NOT EXISTS (
            SELECT 1
            FROM research_projects AS rp
            WHERE rp.id = rr.project_id
              AND rp.status = 'published'
        )
        """
    )


def downgrade() -> None:
    op.alter_column(
        "research_reports",
        "is_public",
        server_default=sa.text("true"),
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )

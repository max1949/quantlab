"""research_reports (研究项目报告, Sprint 8.1)

Revision ID: 0009_research_reports
Revises: 0008_ai_insights
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_research_reports"
down_revision: Union[str, None] = "0008_ai_insights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("grade", sa.String(length=16), nullable=True),
        sa.Column("stages", sa.JSON(), nullable=False),
        sa.Column("narrative", sa.JSON(), nullable=False),
        sa.Column("based_on", sa.JSON(), nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_reports_owner_id"), "research_reports", ["owner_id"])
    op.create_index(op.f("ix_research_reports_factor_id"), "research_reports", ["factor_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_research_reports_factor_id"), table_name="research_reports")
    op.drop_index(op.f("ix_research_reports_owner_id"), table_name="research_reports")
    op.drop_table("research_reports")

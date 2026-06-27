"""ai_insights (AI 研究助手, Sprint 7)

Revision ID: 0008_ai_insights
Revises: 0007_competition
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_ai_insights"
down_revision: Union[str, None] = "0007_competition"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_insights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("target_type", sa.String(length=16), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_insights_owner_id"), "ai_insights", ["owner_id"])
    op.create_index(op.f("ix_ai_insights_target_id"), "ai_insights", ["target_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_insights_target_id"), table_name="ai_insights")
    op.drop_index(op.f("ix_ai_insights_owner_id"), table_name="ai_insights")
    op.drop_table("ai_insights")

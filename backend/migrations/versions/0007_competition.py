"""seasons / submissions (竞技系统, Sprint 6)

Revision ID: 0007_competition
Revises: 0006_validations
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_competition"
down_revision: Union[str, None] = "0006_validations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seasons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_season_name"),
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("season_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("validation_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("base_score", sa.Float(), nullable=False),
        sa.Column("decay_factor", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["validation_id"], ["validations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_id", "validation_id", name="uq_submission_season_validation"),
    )
    op.create_index(op.f("ix_submissions_season_id"), "submissions", ["season_id"])
    op.create_index(op.f("ix_submissions_owner_id"), "submissions", ["owner_id"])
    op.create_index(op.f("ix_submissions_final_score"), "submissions", ["final_score"])


def downgrade() -> None:
    op.drop_index(op.f("ix_submissions_final_score"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_owner_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_season_id"), table_name="submissions")
    op.drop_table("submissions")
    op.drop_table("seasons")

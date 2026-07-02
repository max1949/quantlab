"""factor_scans: parameter grid experiment archive.

Revision ID: 0016_factor_scans
Revises: 0015_private_reports_by_default
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_factor_scans"
down_revision: Union[str, None] = "0015_private_reports_by_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "factor_scans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False, server_default="1d"),
        sa.Column("template_type", sa.String(length=64), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("best_params", sa.JSON(), nullable=True),
        sa.Column("best_score", sa.Float(), nullable=True),
        sa.Column("coach_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("applied_factor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["applied_factor_id"], ["factors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["research_projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_factor_scans_owner_id"), "factor_scans", ["owner_id"], unique=False)
    op.create_index(op.f("ix_factor_scans_project_id"), "factor_scans", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_factor_scans_project_id"), table_name="factor_scans")
    op.drop_index(op.f("ix_factor_scans_owner_id"), table_name="factor_scans")
    op.drop_table("factor_scans")

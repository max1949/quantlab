"""Composite indexes for validation and paper snapshot hot paths.

Revision ID: 0014_perf_indexes
Revises: 0013_paper_tracking
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0014_perf_indexes"
down_revision: Union[str, None] = "0013_paper_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_validations_factor_status_created",
        "validations",
        ["factor_id", "status", "created_at"],
    )
    op.create_index(
        "ix_paper_snapshots_factor_owner_date",
        "paper_snapshots",
        ["factor_id", "owner_id", "as_of_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_paper_snapshots_factor_owner_date", table_name="paper_snapshots")
    op.drop_index("ix_validations_factor_status_created", table_name="validations")

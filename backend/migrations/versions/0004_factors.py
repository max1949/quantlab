"""factors 表 (因子实验室, Sprint 3)

用户创建的因子定义 (template / stack), JSON spec + 版本号。

Revision ID: 0004_factors
Revises: 0003_academy
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_factors"
down_revision: Union[str, None] = "0003_academy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "factors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("template_type", sa.String(length=64), nullable=True),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_factor_owner_name"),
    )
    op.create_index(
        op.f("ix_factors_owner_id"), "factors", ["owner_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_factors_owner_id"), table_name="factors")
    op.drop_table("factors")

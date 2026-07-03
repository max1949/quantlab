"""org_invites: organization invite links.

Revision ID: 0019_org_invites
Revises: 0018_research_orgs
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_org_invites"
down_revision: Union[str, None] = "0018_research_orgs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "org_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=96), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="member"),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["org_id"], ["research_orgs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_org_invites_org_id"), "org_invites", ["org_id"], unique=False)
    op.create_index(op.f("ix_org_invites_token"), "org_invites", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_org_invites_token"), table_name="org_invites")
    op.drop_index(op.f("ix_org_invites_org_id"), table_name="org_invites")
    op.drop_table("org_invites")

"""research_orgs: institutional team factor library.

Revision ID: 0018_research_orgs
Revises: 0017_audit_events
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_research_orgs"
down_revision: Union[str, None] = "0017_audit_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_orgs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_research_orgs_owner_id"), "research_orgs", ["owner_id"], unique=False)
    op.create_index(op.f("ix_research_orgs_slug"), "research_orgs", ["slug"], unique=True)

    op.create_table(
        "org_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="member"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["research_orgs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_member"),
    )
    op.create_index(op.f("ix_org_members_org_id"), "org_members", ["org_id"], unique=False)
    op.create_index(op.f("ix_org_members_user_id"), "org_members", ["user_id"], unique=False)

    op.create_table(
        "org_factor_shares",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("shared_by", sa.Uuid(), nullable=True),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["factor_id"], ["factors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["research_orgs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "factor_id", name="uq_org_factor_share"),
    )
    op.create_index(op.f("ix_org_factor_shares_org_id"), "org_factor_shares", ["org_id"], unique=False)
    op.create_index(op.f("ix_org_factor_shares_factor_id"), "org_factor_shares", ["factor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_org_factor_shares_factor_id"), table_name="org_factor_shares")
    op.drop_index(op.f("ix_org_factor_shares_org_id"), table_name="org_factor_shares")
    op.drop_table("org_factor_shares")
    op.drop_index(op.f("ix_org_members_user_id"), table_name="org_members")
    op.drop_index(op.f("ix_org_members_org_id"), table_name="org_members")
    op.drop_table("org_members")
    op.drop_index(op.f("ix_research_orgs_slug"), table_name="research_orgs")
    op.drop_index(op.f("ix_research_orgs_owner_id"), table_name="research_orgs")
    op.drop_table("research_orgs")

"""Growth OS: users 增长字段 + referrals/templates/shares/follows/events + challenge 升级 (Sprint 9A)

Revision ID: 0011_growth_os
Revises: 0010_research_os
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_growth_os"
down_revision: Union[str, None] = "0010_research_os"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users: 增长字段 ---
    op.add_column("users", sa.Column("reward_points", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("research_contribution_score", sa.Float(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("user_type", sa.String(length=16), server_default="newbie", nullable=False))
    op.add_column("users", sa.Column("onboarding_done", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("users", sa.Column("referred_by", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_users_referred_by", "users", "users", ["referred_by"], ["id"], ondelete="SET NULL")

    # --- referrals (每个被邀请者一条) ---
    op.create_table(
        "referrals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("referrer_id", sa.Uuid(), nullable=False),
        sa.Column("invitee_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="registered", nullable=False),
        sa.Column("reward_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["referrer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invitee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invitee_id", name="uq_referral_invitee"),
    )
    op.create_index(op.f("ix_referrals_referrer_id"), "referrals", ["referrer_id"])
    op.create_index(op.f("ix_referrals_invitee_id"), "referrals", ["invitee_id"])

    # --- research_templates ---
    op.create_table(
        "research_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("factor_template", sa.String(length=32), nullable=False),
        sa.Column("default_params", sa.JSON(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_research_template_code"),
    )
    op.create_index(op.f("ix_research_templates_code"), "research_templates", ["code"], unique=True)

    # --- research_shares ---
    op.create_table(
        "research_shares",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=24), nullable=False),
        sa.Column("card", sa.JSON(), nullable=False),
        sa.Column("views", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["research_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_research_share_token"),
    )
    op.create_index(op.f("ix_research_shares_report_id"), "research_shares", ["report_id"])
    op.create_index(op.f("ix_research_shares_owner_id"), "research_shares", ["owner_id"])
    op.create_index(op.f("ix_research_shares_token"), "research_shares", ["token"], unique=True)

    # --- user_follows ---
    op.create_table(
        "user_follows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("follower_id", sa.Uuid(), nullable=False),
        sa.Column("followee_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["followee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follower_id", "followee_id", name="uq_user_follow"),
    )
    op.create_index(op.f("ix_user_follows_follower_id"), "user_follows", ["follower_id"])
    op.create_index(op.f("ix_user_follows_followee_id"), "user_follows", ["followee_id"])

    # --- user_events ---
    op.create_table(
        "user_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event", sa.String(length=64), nullable=False),
        sa.Column("props", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_events_user_id"), "user_events", ["user_id"])
    op.create_index(op.f("ix_user_events_event"), "user_events", ["event"])

    # --- challenges / challenge_progress 升级 ---
    op.add_column("challenges", sa.Column("user_type", sa.String(length=16), nullable=True))
    op.add_column("challenge_progress", sa.Column("rewarded", sa.JSON(), nullable=True))
    op.add_column("challenge_progress", sa.Column("certificate_code", sa.String(length=40), nullable=True))
    op.add_column("challenge_progress", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    # 回填已有进度的 rewarded 为空列表, 再置非空。
    op.execute("UPDATE challenge_progress SET rewarded = '[]'::json WHERE rewarded IS NULL")
    op.alter_column("challenge_progress", "rewarded", nullable=False, server_default="[]")


def downgrade() -> None:
    op.drop_column("challenge_progress", "completed_at")
    op.drop_column("challenge_progress", "certificate_code")
    op.drop_column("challenge_progress", "rewarded")
    op.drop_column("challenges", "user_type")

    op.drop_index(op.f("ix_user_events_event"), table_name="user_events")
    op.drop_index(op.f("ix_user_events_user_id"), table_name="user_events")
    op.drop_table("user_events")

    op.drop_index(op.f("ix_user_follows_followee_id"), table_name="user_follows")
    op.drop_index(op.f("ix_user_follows_follower_id"), table_name="user_follows")
    op.drop_table("user_follows")

    op.drop_index(op.f("ix_research_shares_token"), table_name="research_shares")
    op.drop_index(op.f("ix_research_shares_owner_id"), table_name="research_shares")
    op.drop_index(op.f("ix_research_shares_report_id"), table_name="research_shares")
    op.drop_table("research_shares")

    op.drop_index(op.f("ix_research_templates_code"), table_name="research_templates")
    op.drop_table("research_templates")

    op.drop_index(op.f("ix_referrals_invitee_id"), table_name="referrals")
    op.drop_index(op.f("ix_referrals_referrer_id"), table_name="referrals")
    op.drop_table("referrals")

    op.drop_constraint("fk_users_referred_by", "users", type_="foreignkey")
    op.drop_column("users", "referred_by")
    op.drop_column("users", "onboarding_done")
    op.drop_column("users", "user_type")
    op.drop_column("users", "research_contribution_score")
    op.drop_column("users", "reward_points")

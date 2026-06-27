"""research_projects / nodes / edges / challenges + 报告升级 + 因子 project_id (Sprint 8)

Revision ID: 0010_research_os
Revises: 0009_research_reports
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_research_os"
down_revision: Union[str, None] = "0009_research_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 研究项目 (顶层容器) ---
    op.create_table(
        "research_projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="draft", nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_projects_owner_id"), "research_projects", ["owner_id"])

    # --- 研究路径图谱 ---
    op.create_table(
        "research_nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("ref_type", sa.String(length=20), nullable=True),
        sa.Column("ref_id", sa.Uuid(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["research_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_nodes_project_id"), "research_nodes", ["project_id"])

    op.create_table(
        "research_edges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("from_node", sa.Uuid(), nullable=False),
        sa.Column("to_node", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["research_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_node"], ["research_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_node"], ["research_nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_edges_project_id"), "research_edges", ["project_id"])

    # --- 30 天挑战 ---
    op.create_table(
        "challenges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("days", sa.Integer(), server_default="30", nullable=False),
        sa.Column("milestones", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_challenge_code"),
    )
    op.create_index(op.f("ix_challenges_code"), "challenges", ["code"], unique=True)

    op.create_table(
        "challenge_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("challenge_id", sa.Uuid(), nullable=False),
        sa.Column("completed", sa.JSON(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "challenge_id", name="uq_challenge_progress"),
    )
    op.create_index(op.f("ix_challenge_progress_user_id"), "challenge_progress", ["user_id"])
    op.create_index(op.f("ix_challenge_progress_challenge_id"), "challenge_progress", ["challenge_id"])

    # --- 因子归属项目 ---
    op.add_column("factors", sa.Column("project_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_factors_project_id"), "factors", ["project_id"])
    op.create_foreign_key(
        "fk_factors_project", "factors", "research_projects", ["project_id"], ["id"], ondelete="SET NULL"
    )

    # --- 研究报告升级 ---
    op.add_column("research_reports", sa.Column("project_id", sa.Uuid(), nullable=True))
    op.add_column("research_reports", sa.Column("factor_version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("research_reports", sa.Column("summary", sa.Text(), server_default="", nullable=False))
    op.add_column("research_reports", sa.Column("methodology", sa.Text(), server_default="", nullable=False))
    op.add_column("research_reports", sa.Column("result", sa.Text(), server_default="", nullable=False))
    op.add_column("research_reports", sa.Column("risk_analysis", sa.Text(), server_default="", nullable=False))
    op.add_column("research_reports", sa.Column("improvement_suggestion", sa.Text(), server_default="", nullable=False))
    op.create_index(op.f("ix_research_reports_project_id"), "research_reports", ["project_id"])
    op.create_foreign_key(
        "fk_research_reports_project", "research_reports", "research_projects", ["project_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_research_reports_project", "research_reports", type_="foreignkey")
    op.drop_index(op.f("ix_research_reports_project_id"), table_name="research_reports")
    for col in ("improvement_suggestion", "risk_analysis", "result", "methodology", "summary", "factor_version", "project_id"):
        op.drop_column("research_reports", col)

    op.drop_constraint("fk_factors_project", "factors", type_="foreignkey")
    op.drop_index(op.f("ix_factors_project_id"), table_name="factors")
    op.drop_column("factors", "project_id")

    op.drop_index(op.f("ix_challenge_progress_challenge_id"), table_name="challenge_progress")
    op.drop_index(op.f("ix_challenge_progress_user_id"), table_name="challenge_progress")
    op.drop_table("challenge_progress")
    op.drop_index(op.f("ix_challenges_code"), table_name="challenges")
    op.drop_table("challenges")

    op.drop_index(op.f("ix_research_edges_project_id"), table_name="research_edges")
    op.drop_table("research_edges")
    op.drop_index(op.f("ix_research_nodes_project_id"), table_name="research_nodes")
    op.drop_table("research_nodes")
    op.drop_index(op.f("ix_research_projects_owner_id"), table_name="research_projects")
    op.drop_table("research_projects")

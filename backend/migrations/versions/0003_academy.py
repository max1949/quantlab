"""academy: tasks/user_tasks + users.experience (Sprint 2)

- users 增加 experience 列 (累计经验, 驱动等级成长)
- 新建 tasks (学院任务) 与 user_tasks (完成记录) 表

Revision ID: 0003_academy
Revises: 0002_users
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_academy"
down_revision: Union[str, None] = "0002_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "experience", sa.Integer(), server_default="0", nullable=False
        ),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column(
            "min_level", sa.SmallInteger(), server_default="0", nullable=False
        ),
        sa.Column(
            "xp_reward", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "order_index", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_code"), "tasks", ["code"], unique=True)

    op.create_table(
        "user_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "task_id", name="uq_user_task"),
    )
    op.create_index(
        op.f("ix_user_tasks_user_id"), "user_tasks", ["user_id"]
    )
    op.create_index(
        op.f("ix_user_tasks_task_id"), "user_tasks", ["task_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_tasks_task_id"), table_name="user_tasks")
    op.drop_index(op.f("ix_user_tasks_user_id"), table_name="user_tasks")
    op.drop_table("user_tasks")
    op.drop_index(op.f("ix_tasks_code"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_column("users", "experience")

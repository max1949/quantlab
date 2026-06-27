"""baseline (空基线)

建立迁移链起点。Sprint 1 不创建业务表 —— 表结构随各 Sprint 的
ORM 模型通过 autogenerate 增量迁移。此基线仅保证 `alembic upgrade head`
可在全新数据库上成功执行。

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

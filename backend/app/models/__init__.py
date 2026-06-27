# ORM 模型包。
# 模型需在此导入, 以便 Alembic autogenerate 能发现 (env.py 会 import 本包)。
from backend.app.models.user import User, UserLevel  # noqa: F401

__all__ = ["User", "UserLevel"]

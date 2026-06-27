"""数据库会话与 ORM 基类。

骨架阶段只提供引擎 / Session 工厂 / Base。具体 ORM 模型在 backend/app/models/
中按 Sprint 定义, 并由 Alembic 迁移落地。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。"""


def get_db() -> Generator:
    """FastAPI 依赖: 提供请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

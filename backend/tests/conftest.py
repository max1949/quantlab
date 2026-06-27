"""测试夹具。

用 SQLite 内存库替代 PostgreSQL, 让用户系统的接口测试不依赖外部服务。
User 模型用 ``sa.Uuid`` 等跨方言类型, 在 SQLite 下同样可建表。
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.main import app
import backend.app.models  # noqa: F401  注册 ORM 模型到 Base.metadata


@pytest.fixture()
def db_session() -> Generator:
    # StaticPool + 共享连接: 让 :memory: 库在整个测试用例期间保持同一份数据。
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session) -> Generator:
    def _override_get_db() -> Generator:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()

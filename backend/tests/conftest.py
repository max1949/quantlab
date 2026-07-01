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

from backend.app.core.config import get_settings
from backend.app.core.database import Base, get_db
from backend.app.main import app
import backend.app.models  # noqa: F401  注册 ORM 模型到 Base.metadata


@pytest.fixture(autouse=True)
def _test_settings(tmp_path_factory) -> Generator:
    """测试期配置: 回测同步执行 (eager, 不需 worker); 行情数据写临时目录。"""
    settings = get_settings()
    prev_eager = settings.celery_task_always_eager
    prev_dir = settings.market_data_dir
    settings.celery_task_always_eager = True
    settings.market_data_dir = str(tmp_path_factory.mktemp("market_data"))
    settings.captcha_disabled = True
    settings.rate_limit_disabled = True
    try:
        yield
    finally:
        settings.celery_task_always_eager = prev_eager
        settings.market_data_dir = prev_dir
        settings.captcha_disabled = False
        settings.rate_limit_disabled = False


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

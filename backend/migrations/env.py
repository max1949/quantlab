"""Alembic 迁移环境。

- 连接串从应用配置 (settings.database_url) 读取, 与 .env 保持单一来源。
- target_metadata 绑定 ORM Base.metadata, 支持 autogenerate。
  模型在 backend/app/models/ 定义后, 需在 backend/app/models/__init__.py 中导入,
  Alembic 才能在 autogenerate 时发现它们。
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import get_settings
from backend.app.core.database import Base
import backend.app.models  # noqa: F401  确保模型被导入以供 autogenerate

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 注入运行时数据库连接串
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

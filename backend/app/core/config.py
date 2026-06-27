"""应用配置。

通过环境变量 / .env 注入 (pydantic-settings)。骨架阶段仅声明基础项,
后续 Sprint 在此追加各模块所需配置。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "QuantLab AI"

    # 数据库
    database_url: str = "postgresql+psycopg://quantlab:quantlab@localhost:5432/quantlab"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # 认证
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # 行情数据目录 (V1: Parquet 存储)
    market_data_dir: str = "/app/data/market_data"


@lru_cache
def get_settings() -> Settings:
    return Settings()

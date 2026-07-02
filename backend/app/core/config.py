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
    # 站点对外地址 (用于 SEO canonical / sitemap 绝对 URL)。留空则按请求推断。
    public_base_url: str = ""

    # 数据库
    database_url: str = "postgresql+psycopg://quantlab:quantlab@localhost:5432/quantlab"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # 认证
    secret_key: str = "change-me-in-production"
    captcha_secret: str = ""
    captcha_disabled: bool = False
    rate_limit_disabled: bool = False
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # 行情数据目录 (V1: Parquet 存储)。相对路径: 从运行 cwd 解析,
    # 本机原生从仓库根运行 -> data/market_data; Docker cwd=/app -> /app/data/market_data。
    market_data_dir: str = "data/market_data"

    # Celery eager 模式: True 时任务同步执行 (测试用, 不需 worker)。
    celery_task_always_eager: bool = False

    # AI 研究助手 (Sprint 7): 外部 LLM (OpenAI 兼容接口)。
    # 未配置 api_key 时自动降级为 engine 本地规则分析 (无网络也可用)。
    ai_enabled: bool = True               # 总开关
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""                 # 留空 -> 走本地降级
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 30.0
    # 卡密池 (与 ai.ziyingke.com 共用 Supabase membership_cards)
    card_pool_supabase_url: str = ""
    card_pool_service_key: str = ""
    # Optional: direct Postgres URI for one-time Supabase DDL (card pool migration)
    card_pool_database_url: str = ""

    # 运营批量发卡 (留空则禁用 /admin/billing 接口)
    admin_api_key: str = ""

    # 研究质量闸门 (发布/分享)
    research_gate_enabled: bool = True
    sealed_holdout_ratio: float = 0.15
    publish_min_oos_sharpe: float = 0.15
    publish_min_robustness_score: float = 50.0
    publish_min_backtest_sharpe: float = 0.0
    publish_require_sealed_holdout: bool = True
    publish_min_sealed_holdout_sharpe: float = 0.0
    publish_min_robustness_grades: str = "稳健,中等"

    # 纸面跟踪
    paper_tracking_bars: int = 120

    # Python 因子沙箱
    sandbox_timeout_sec: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

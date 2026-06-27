# ORM 模型包。
# 模型需在此导入, 以便 Alembic autogenerate 能发现 (env.py 会 import 本包)。
from backend.app.models.ai import (  # noqa: F401
    AiInsight,
    InsightKind,
    InsightSource,
)
from backend.app.models.backtest import Backtest, BacktestStatus  # noqa: F401
from backend.app.models.competition import (  # noqa: F401
    Season,
    SeasonStatus,
    Submission,
)
from backend.app.models.factor import Factor, FactorKind  # noqa: F401
from backend.app.models.market import DataSnapshot, MarketDataset  # noqa: F401
from backend.app.models.task import Task, TaskStatus, UserTask  # noqa: F401
from backend.app.models.user import User, UserLevel  # noqa: F401
from backend.app.models.validation import Validation, ValidationStatus  # noqa: F401

__all__ = [
    "User",
    "UserLevel",
    "Task",
    "UserTask",
    "TaskStatus",
    "Factor",
    "FactorKind",
    "MarketDataset",
    "DataSnapshot",
    "Backtest",
    "BacktestStatus",
    "Validation",
    "ValidationStatus",
    "Season",
    "SeasonStatus",
    "Submission",
    "AiInsight",
    "InsightKind",
    "InsightSource",
]

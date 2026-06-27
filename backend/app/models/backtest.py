"""回测模型 (Sprint 4)。

一次回测绑定 (因子版本 + 数据快照 + 成本配置), 产出指标 / 净值 / 研究报告。
重计算异步执行 (Celery), 故有状态机: pending -> running -> success/failed。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class BacktestStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Backtest(Base):
    """一次回测任务及其结果。"""

    __tablename__ = "backtests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    factor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factors.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("data_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default=BacktestStatus.PENDING.value,
        server_default="pending",
        nullable=False,
    )

    cost_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    equity_curve: Mapped[list | None] = mapped_column(JSON, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

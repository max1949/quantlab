"""科学验证模型 (Sprint 5)。

把"一次回测"升级为"可信验证": 样本外 (OOS) + Walk-Forward + 参数敏感性,
汇总成稳健性评分。与回测一样重计算异步执行 (Celery), 绑定数据快照保证可复现。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Validation(Base):
    """对某因子在某品种上的科学验证及其结果。"""

    __tablename__ = "validations"

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
        default=ValidationStatus.PENDING.value,
        server_default="pending",
        nullable=False,
    )

    cost_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    oos_ratio: Mapped[float] = mapped_column(
        Float, default=0.3, server_default="0.3", nullable=False
    )
    n_splits: Mapped[int] = mapped_column(
        Integer, default=4, server_default="4", nullable=False
    )

    oos: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    walk_forward: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sensitivity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    robustness: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

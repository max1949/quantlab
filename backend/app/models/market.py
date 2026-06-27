"""行情数据索引与数据快照模型 (Sprint 4)。

数据存储 V1: PostgreSQL 存索引 + Parquet 存 K 线。
- `MarketDataset`: 某品种的 Parquet 文件索引 (品种/周期/区间/行数/路径)。
- `DataSnapshot`: 回测所用数据的不可变快照 (区间 + 内容哈希), 保证结果可复现。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class MarketDataset(Base):
    """行情数据集索引 (一条 = 一个品种的一份 Parquet)。"""

    __tablename__ = "market_datasets"
    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", name="uq_dataset_symbol_tf"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(
        String(16), default="1d", server_default="1d", nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    rows: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DataSnapshot(Base):
    """回测数据快照 (可复现): 记录所用数据的区间与内容哈希。"""

    __tablename__ = "data_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(
        String(16), default="1d", server_default="1d", nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    rows: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

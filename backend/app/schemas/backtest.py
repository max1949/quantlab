"""回测与行情数据集的出入参 schema (Sprint 4)。"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    timeframe: str
    start_date: date
    end_date: date
    rows: int


class BacktestCreate(BaseModel):
    """创建回测入参。"""

    factor_id: uuid.UUID
    symbol: str
    fee_rate: float = Field(default=0.0005, ge=0, le=0.1)
    slippage_bps: float = Field(default=1.0, ge=0, le=1000)


class BacktestSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    factor_id: uuid.UUID
    symbol: str
    status: str
    metrics: dict | None
    created_at: datetime
    finished_at: datetime | None


class BacktestDetail(BacktestSummary):
    owner_id: uuid.UUID
    snapshot_id: uuid.UUID | None
    cost_config: dict
    equity_curve: list | None
    report: dict | None
    error: str | None

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
    effective_rows: int | None = None
    tier_cap: int | None = None


class DataQualityOut(BaseModel):
    symbol: str
    timeframe: str
    passed: bool
    grade: str
    warnings: list[str]
    stats: dict


class BacktestCreate(BaseModel):
    """创建回测入参。"""

    factor_id: uuid.UUID
    symbol: str
    timeframe: str = Field(default="1d", pattern=r"^[0-9]+[mhdw]$")
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
    academy_rewards: list = Field(default_factory=list)
    market_regime: dict | None = None


class CrossSectionBacktestCreate(BaseModel):
    """L2: 截面多标的回测入参。"""

    factor_id: uuid.UUID
    symbols: list[str] = Field(default_factory=lambda: ["RB", "AU", "IF"], min_length=2)
    top_n: int = Field(default=1, ge=1, le=10)
    long_short: bool = True
    fee_rate: float = Field(default=0.0005, ge=0, le=0.1)
    slippage_bps: float = Field(default=1.0, ge=0, le=1000)


class CrossSectionBacktestOut(BaseModel):
    factor_id: uuid.UUID
    factor_name: str
    symbols: list[str]
    top_n: int
    long_short: bool
    metrics: dict
    equity_curve: list
    latest_weights: dict[str, float | None]


class CostSensitivityCreate(BaseModel):
    """L2: 成本敏感性分析入参。"""

    factor_id: uuid.UUID
    symbol: str
    fee_rates: list[float] = Field(default_factory=lambda: [0.0, 0.0002, 0.0005, 0.001])
    slippage_bps_values: list[float] = Field(default_factory=lambda: [0.0, 1.0, 3.0, 5.0])


class CostSensitivityPoint(BaseModel):
    fee_rate: float
    slippage_bps: float
    metrics: dict


class CostSensitivityOut(BaseModel):
    factor_id: uuid.UUID
    factor_name: str
    symbol: str
    results: list[CostSensitivityPoint]

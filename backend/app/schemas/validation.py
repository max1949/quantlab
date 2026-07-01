"""科学验证出入参 schema (Sprint 5)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValidationCreate(BaseModel):
    factor_id: uuid.UUID
    symbol: str
    timeframe: str = Field(default="1d", pattern=r"^[0-9]+[mhdw]$")
    fee_rate: float = Field(default=0.0005, ge=0, le=0.1)
    slippage_bps: float = Field(default=1.0, ge=0, le=1000)
    oos_ratio: float = Field(default=0.3, gt=0.05, lt=0.9)
    n_splits: int = Field(default=4, ge=2, le=12)


class ValidationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    factor_id: uuid.UUID
    symbol: str
    status: str
    robustness: dict | None
    created_at: datetime
    finished_at: datetime | None


class ValidationDetail(ValidationSummary):
    owner_id: uuid.UUID
    snapshot_id: uuid.UUID | None
    cost_config: dict
    oos_ratio: float
    n_splits: int
    oos: dict | None
    walk_forward: dict | None
    sensitivity: dict | None
    error: str | None


class OrthogonalizeCreate(BaseModel):
    target_factor_id: uuid.UUID
    control_factor_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)
    symbol: str


class OrthogonalizeOut(BaseModel):
    target_factor_id: uuid.UUID
    target_factor_name: str
    control_factors: list[dict]
    symbol: str
    result: dict


class RobustnessTestCreate(BaseModel):
    factor_id: uuid.UUID
    symbol: str
    fee_rate: float = Field(default=0.0005, ge=0, le=0.1)
    slippage_bps: float = Field(default=1.0, ge=0, le=1000)


class RobustnessTestOut(BaseModel):
    factor_id: uuid.UUID
    factor_name: str
    symbol: str
    sensitivity: dict
    verdict: dict


class OverfitCheckCreate(BaseModel):
    factor_id: uuid.UUID
    symbol: str
    fee_rate: float = Field(default=0.0005, ge=0, le=0.1)
    slippage_bps: float = Field(default=1.0, ge=0, le=1000)
    oos_ratio: float = Field(default=0.3, gt=0.05, lt=0.9)
    n_splits: int = Field(default=4, ge=2, le=12)


class OverfitCheckOut(BaseModel):
    factor_id: uuid.UUID
    factor_name: str
    symbol: str
    oos: dict
    walk_forward: dict
    sensitivity: dict
    overfit: dict

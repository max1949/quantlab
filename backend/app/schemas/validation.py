"""科学验证出入参 schema (Sprint 5)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValidationCreate(BaseModel):
    factor_id: uuid.UUID
    symbol: str
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

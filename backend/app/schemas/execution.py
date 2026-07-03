"""执行适配层 schemas。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PaperOrderCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    side: str = Field(pattern=r"^(buy|sell)$")
    notional_cny: float = Field(gt=0, le=50_000_000)
    factor_id: uuid.UUID | None = None
    signal_value: float | None = None
    note: str = Field(default="", max_length=200)


class PaperOrderOut(BaseModel):
    id: uuid.UUID
    factor_id: uuid.UUID | None
    symbol: str
    side: str
    notional_cny: float
    status: str
    signal_value: float | None
    regime: str | None
    regime_fit_score: int | None
    note: str
    created_at: datetime

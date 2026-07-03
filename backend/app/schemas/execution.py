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
    channel: str = Field(default="paper", pattern=r"^(paper|vnpy|qmt)$")
    acknowledge_risk: bool = False


class RiskCheckIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    notional_cny: float = Field(gt=0, le=50_000_000)
    channel: str = Field(default="paper", pattern=r"^(paper|vnpy|qmt)$")
    factor_id: uuid.UUID | None = None
    acknowledge_risk: bool = False


class ExecutionConfigOut(BaseModel):
    kill_switch: bool
    max_notional_cny: float
    min_regime_fit_vnpy: int
    vnpy_configured: bool
    qmt_configured: bool = False
    channels: list[dict]


class GatewayWebhookIn(BaseModel):
    external_ref: str
    status: str


class RiskCheckOut(BaseModel):
    allowed: bool
    message: str
    channel: str
    regime: dict | None = None
    risk: dict


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
    channel: str
    external_ref: str | None
    risk_verdict: str
    risk_detail: str
    gateway_status: str | None
    filled_at: datetime | None
    routed_at: datetime | None
    note: str
    created_at: datetime


class OrgPaperOrderOut(PaperOrderOut):
    username: str


class PaperOrderEventOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    event_type: str
    from_status: str | None
    to_status: str | None
    gateway_status: str | None
    detail: str
    created_at: datetime

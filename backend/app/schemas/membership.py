"""会员 / 计费相关 Pydantic 模型 (Sprint 10)。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PlanOut(BaseModel):
    code: str
    name: str
    tier: int
    price_cny: int
    period_days: int
    tagline: str
    features: list[str]
    kind: str = "personal"
    seats: int | None = None


class SubscriptionStatusOut(BaseModel):
    tier: int
    tier_name: str
    plan_code: str
    expires_at: datetime | None
    is_paid: bool
    personal_tier: int = 0
    org_tier: int = 0
    org_benefit: bool = False


class FeatureState(BaseModel):
    key: str
    label: str
    allowed: bool
    level_ok: bool
    tier_ok: bool
    min_level: int
    min_level_name: str
    min_tier: int
    min_tier_name: str


class MarketDataEntitlement(BaseModel):
    allowed_timeframes: list[str]
    limits: dict
    summary: str


class EntitlementsOut(BaseModel):
    level: int
    level_name: str
    tier: int
    tier_name: str
    features: list[FeatureState]
    market_data: MarketDataEntitlement


class RedeemIn(BaseModel):
    code: str


class RedeemOut(BaseModel):
    ok: bool
    tier: int
    tier_name: str
    expires_at: datetime | None
    message: str


class CheckoutIn(BaseModel):
    plan_code: str


class CheckoutOut(BaseModel):
    configured: bool
    plan_code: str
    plan_name: str
    price_cny: int
    message: str
    pay_url: str | None = None
    org_id: str | None = None

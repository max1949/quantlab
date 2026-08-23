"""Strategy Specification models (source of truth; not raw Python strategy files)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class MarketSpec(BaseModel):
    instrument: str
    venue: str = "SIM"
    asset_class: str = "FX"
    timeframe: str = "15m"
    session: str | None = None
    timezone: str = "UTC"


class DataSpec(BaseModel):
    required: list[str] = Field(default_factory=lambda: ["bars"])
    warmup: int = 50
    frequency: str = "15m"
    source_policy: str = "BROKER_SPECIFIC_DATA"


class ConditionSpec(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class SideEntrySpec(BaseModel):
    conditions: list[ConditionSpec] = Field(default_factory=list)


class EntrySpec(BaseModel):
    long: SideEntrySpec = Field(default_factory=SideEntrySpec)
    short: SideEntrySpec = Field(default_factory=SideEntrySpec)


class ExitSpec(BaseModel):
    conditions: list[ConditionSpec] = Field(default_factory=list)


class StopLossSpec(BaseModel):
    type: str = "none"
    value: float | None = None


class TakeProfitSpec(BaseModel):
    type: str = "none"
    value: float | None = None


class PositionSizingSpec(BaseModel):
    type: str = "fixed"
    risk_per_trade: float | None = None
    max_position: float | None = None
    trade_size: str = "1000000"


class RiskSpec(BaseModel):
    daily_loss_limit: float | None = None
    max_drawdown: float | None = None
    max_open_positions: int | None = 1
    max_consecutive_losses: int | None = None
    exposure_limit: float | None = None
    leverage_limit: float | None = None


class ExecutionSpec(BaseModel):
    order_type: str = "MARKET"
    time_in_force: str = "GTC"
    slippage_policy: str = "model_default"
    retry_policy: str = "none"


class RegimeSpec(BaseModel):
    enabled: bool = False
    allow: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)


class ValidationSpec(BaseModel):
    required_tests: list[str] = Field(default_factory=list)


class DeploymentSpec(BaseModel):
    permitted_environments: list[str] = Field(default_factory=lambda: ["BACKTEST"])

    @field_validator("permitted_environments")
    @classmethod
    def _no_live_by_default(cls, v: list[str]) -> list[str]:
        # Phase 2: LIVE must never be silently present without explicit later gates.
        return v


class StrategyMeta(BaseModel):
    id: str
    version: str
    name: str
    description: str = ""
    author: str = "quantlab"
    status: Literal[
        "DRAFT",
        "RESEARCH",
        "VALIDATED",
        "PAPER",
        "SHADOW",
        "LIVE_APPROVED",
        "LIVE",
        "SUSPENDED",
        "RETIRED",
    ] = "DRAFT"
    parent_version: str | None = None
    change_reason: str | None = None
    created_by: str = "system"
    ai_generated: bool = False
    user_approved: bool = False
    backtest_id: str | None = None
    validation_id: str | None = None
    deployment_id: str | None = None
    assumed_values: list[str] = Field(default_factory=list)
    ambiguous: bool = False
    deployable: bool = False


class StrategySpec(BaseModel):
    strategy: StrategyMeta
    market: MarketSpec
    data: DataSpec = Field(default_factory=DataSpec)
    entry: EntrySpec = Field(default_factory=EntrySpec)
    exit: ExitSpec = Field(default_factory=ExitSpec)
    stop_loss: StopLossSpec = Field(default_factory=StopLossSpec)
    take_profit: TakeProfitSpec = Field(default_factory=TakeProfitSpec)
    position_sizing: PositionSizingSpec = Field(default_factory=PositionSizingSpec)
    risk: RiskSpec = Field(default_factory=RiskSpec)
    execution: ExecutionSpec = Field(default_factory=ExecutionSpec)
    regime: RegimeSpec = Field(default_factory=RegimeSpec)
    validation: ValidationSpec = Field(default_factory=ValidationSpec)
    deployment: DeploymentSpec = Field(default_factory=DeploymentSpec)

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def content_hash(self) -> str:
        """Hash excluding mutable approval/status metadata that should not rewrite history."""
        payload = self.canonical_dict()
        meta = payload["strategy"]
        for k in (
            "status",
            "user_approved",
            "backtest_id",
            "validation_id",
            "deployment_id",
            "change_reason",
            "created_by",
        ):
            meta.pop(k, None)
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def bump_version(self, new_version: str, *, change_reason: str, created_by: str) -> StrategySpec:
        data = self.canonical_dict()
        parent = data["strategy"]["version"]
        data["strategy"]["parent_version"] = parent
        data["strategy"]["version"] = new_version
        data["strategy"]["change_reason"] = change_reason
        data["strategy"]["created_by"] = created_by
        data["strategy"]["status"] = "DRAFT"
        data["strategy"]["user_approved"] = False
        data["strategy"]["deployable"] = False
        return StrategySpec.model_validate(data)

"""Strategy Spec v2 schema — business definition independent of Nautilus internals."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from engine.domain.defaults import CANONICAL_EMA_DEFAULT_FAST, CANONICAL_EMA_DEFAULT_SLOW
from engine.domain.hashing import hash_strategy_definition
from engine.strategies.v2.errors import SpecV2Error


class IdentityV2(BaseModel):
    strategy_id: str
    version: str
    name: str
    family_id: str | None = None
    parent_version: str | None = None
    derived_from: str | None = None
    fork_of: str | None = None
    schema_version: Literal["2.0"] = "2.0"


class MetadataV2(BaseModel):
    description: str = ""
    author: str = "quantlab"
    tags: list[str] = Field(default_factory=list)
    ai_generated: bool = False
    user_approved: bool = False
    ambiguous: bool = False
    change_reason: str | None = None
    created_by: str = "system"
    # Display-only; excluded from content hash via hashing policy when nested under excluded keys
    display_name_zh: str | None = None


class UniverseV2(BaseModel):
    instruments: list[str]
    venue: str = "SIM"
    venue_class: str = "SIMULATED"
    asset_class: str = "FX"
    quote_currency: str | None = None
    base_currency: str | None = None
    synthetic_formula: str | None = None

    @field_validator("instruments")
    @classmethod
    def _nonempty(cls, v: list[str]) -> list[str]:
        if not v or not any(i.strip() for i in v):
            raise ValueError("universe.instruments required")
        return v


class TimeframeV2(BaseModel):
    timeframe: str
    bar_type: Literal["bars", "ticks", "book"] = "bars"
    timezone: str = "UTC"
    session: str | None = None
    calendar: str | None = None
    bar_boundary: str = "left_open_right_closed"


class DataRequirementsV2(BaseModel):
    required: list[str] = Field(default_factory=lambda: ["bars"])
    warmup: int = 50
    frequency: str = "15m"
    source_policy: str = "PUBLIC_OR_BROKER"
    custom_data: list[str] = Field(default_factory=list)


class ConditionV2(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class SideEntryV2(BaseModel):
    conditions: list[ConditionV2] = Field(default_factory=list)


class SignalLogicV2(BaseModel):
    entry_long: list[ConditionV2] = Field(default_factory=list)
    entry_short: list[ConditionV2] = Field(default_factory=list)
    exit: list[ConditionV2] = Field(default_factory=list)
    filters: list[ConditionV2] = Field(default_factory=list)
    signal_priority: list[str] = Field(default_factory=list)
    allowed_direction: Literal["long_only", "short_only", "both", "flat_only"] = "both"


class PositionSizingV2(BaseModel):
    type: Literal["fixed", "risk_based", "volatility", "percent_equity"] = "fixed"
    trade_size: str = "1"
    risk_per_trade: float | None = None
    max_position: float | None = None
    capital_allocation_ceiling: float | None = None


class StopLossV2(BaseModel):
    type: str = "none"
    value: float | None = None
    trailing: bool = False
    trailing_value: float | None = None


class TakeProfitV2(BaseModel):
    type: str = "none"
    value: float | None = None


class RiskV2(BaseModel):
    daily_loss_limit: float | None = None
    max_drawdown: float | None = None
    max_open_positions: int | None = 1
    max_consecutive_losses: int | None = None
    exposure_limit: float | None = None
    leverage_limit: float | None = None
    risk_per_trade: float | None = None


class AssumptionsV2(BaseModel):
    fee_model: str = "model_default"
    slippage_model: str = "model_default"
    latency_assumption: str = "zero_or_modeled"
    fill_model: str = "next_bar_or_engine_default"


class ExecutionV2(BaseModel):
    order_type: str = "MARKET"
    time_in_force: str = "GTC"
    reduce_only: bool = False
    retry_policy: str = "none"
    assumptions: AssumptionsV2 = Field(default_factory=AssumptionsV2)


class RegimeV2(BaseModel):
    enabled: bool = False
    intended: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    classifier_ref: str | None = None


class CompatibilityV2(BaseModel):
    required_broker_capabilities: list[str] = Field(default_factory=list)
    required_data_capabilities: list[str] = Field(default_factory=list)
    required_engine_features: list[str] = Field(default_factory=lambda: ["ema_cross"])
    permitted_environments: list[str] = Field(
        default_factory=lambda: ["BACKTEST", "PAPER"]
    )

    @field_validator("permitted_environments")
    @classmethod
    def _no_silent_live(cls, v: list[str]) -> list[str]:
        return [str(x).upper() for x in v]


class ParametersV2(BaseModel):
    """Explicit strategy parameters (SSOT for defaults — not UX examples)."""

    values: dict[str, Any] = Field(default_factory=dict)


class ExtensionPointV2(BaseModel):
    name: str
    kind: Literal["filter", "signal", "sizing", "risk", "execution", "other"] = "other"
    required: bool = False
    description: str = ""


class StrategySpecV2(BaseModel):
    """Canonical Strategy Spec v2 — must not embed Nautilus class names as business identity."""

    identity: IdentityV2
    metadata: MetadataV2 = Field(default_factory=MetadataV2)
    universe: UniverseV2
    timeframe: TimeframeV2
    data_requirements: DataRequirementsV2 = Field(default_factory=DataRequirementsV2)
    signal_logic: SignalLogicV2 = Field(default_factory=SignalLogicV2)
    position_sizing: PositionSizingV2 = Field(default_factory=PositionSizingV2)
    stop_loss: StopLossV2 = Field(default_factory=StopLossV2)
    take_profit: TakeProfitV2 = Field(default_factory=TakeProfitV2)
    risk: RiskV2 = Field(default_factory=RiskV2)
    execution: ExecutionV2 = Field(default_factory=ExecutionV2)
    regime: RegimeV2 = Field(default_factory=RegimeV2)
    compatibility: CompatibilityV2 = Field(default_factory=CompatibilityV2)
    parameters: ParametersV2 = Field(default_factory=ParametersV2)
    extension_points: list[ExtensionPointV2] = Field(default_factory=list)
    invariant_ids: list[str] = Field(default_factory=list)
    contract_id: str | None = None
    implementation_ref: str | None = None

    @model_validator(mode="after")
    def _fail_closed(self) -> StrategySpecV2:
        if not self.identity.strategy_id.strip():
            raise ValueError("identity.strategy_id required")
        if not self.identity.version.strip():
            raise ValueError("identity.version required")
        if self.metadata.ambiguous:
            raise ValueError("ambiguous specs are not valid Spec v2 assets (fail closed)")
        if "LIVE" in self.compatibility.permitted_environments and not self.metadata.user_approved:
            raise ValueError("LIVE environment requires metadata.user_approved=true")
        if self.risk.leverage_limit is not None and self.risk.leverage_limit < 0:
            raise ValueError("risk.leverage_limit cannot be negative")
        if self.risk.max_drawdown is not None and (
            self.risk.max_drawdown < 0 or self.risk.max_drawdown > 1
        ):
            raise ValueError("risk.max_drawdown must be in [0, 1] when set")
        return self

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def content_hash(self) -> str:
        payload = self.canonical_dict()
        # Strip display-only metadata from hash
        meta = payload.get("metadata") or {}
        meta.pop("display_name_zh", None)
        meta.pop("change_reason", None)
        meta.pop("created_by", None)
        return hash_strategy_definition(payload)

    def primary_instrument(self) -> str:
        return self.universe.instruments[0]


def validate_spec_v2(data: dict[str, Any] | StrategySpecV2) -> StrategySpecV2:
    if isinstance(data, StrategySpecV2):
        return data
    try:
        return StrategySpecV2.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        raise SpecV2Error(str(exc)) from exc


def extract_ema_params(spec: StrategySpecV2) -> tuple[int, int]:
    """Require explicit ema params in Spec v2 — no silent UX example defaults."""
    for cond in list(spec.signal_logic.entry_long) + list(spec.signal_logic.entry_short):
        if cond.type == "ema_cross":
            if "fast" not in cond.params or "slow" not in cond.params:
                # Allow parameters.values SSOT
                vals = spec.parameters.values
                if "ema_fast" in vals and "ema_slow" in vals:
                    return int(vals["ema_fast"]), int(vals["ema_slow"])
                raise SpecV2Error(
                    "ema_cross requires explicit fast/slow params "
                    f"(canonical defaults documented as {CANONICAL_EMA_DEFAULT_FAST}/"
                    f"{CANONICAL_EMA_DEFAULT_SLOW}; EXAMPLE≠DEFAULT)"
                )
            return int(cond.params["fast"]), int(cond.params["slow"])
    vals = spec.parameters.values
    if "ema_fast" in vals and "ema_slow" in vals:
        return int(vals["ema_fast"]), int(vals["ema_slow"])
    raise SpecV2Error("ema_cross signal not found and parameters.ema_fast/slow missing")

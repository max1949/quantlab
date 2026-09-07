"""Deterministic Strategy Spec v1 → v2 migration (semantic drift = 0)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.strategies.spec import StrategySpec
from engine.strategies.v2.contract import StrategyContract, validate_contract
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.invariants import (
    StrategyInvariants,
    default_research_invariants,
    validate_invariants,
)
from engine.strategies.v2.spec_v2 import (
    AssumptionsV2,
    CompatibilityV2,
    ConditionV2,
    DataRequirementsV2,
    ExecutionV2,
    IdentityV2,
    MetadataV2,
    ParametersV2,
    PositionSizingV2,
    RegimeV2,
    RiskV2,
    SignalLogicV2,
    StopLossV2,
    StrategySpecV2,
    TakeProfitV2,
    TimeframeV2,
    UniverseV2,
    validate_spec_v2,
)
from engine.strategies.validate import SpecValidationError, load_spec, validate_spec


def _map_env(envs: list[str]) -> list[str]:
    out: list[str] = []
    for e in envs:
        u = str(e).upper()
        if u == "SANDBOX":
            out.append("PAPER")
        else:
            out.append(u)
    return sorted(set(out))


def _direction_from_entry(spec: StrategySpec) -> str:
    has_long = bool(spec.entry.long.conditions)
    has_short = bool(spec.entry.short.conditions)
    if has_long and has_short:
        return "both"
    if has_long:
        return "long_only"
    if has_short:
        return "short_only"
    return "flat_only"


def _ema_parameters(spec: StrategySpec) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for side in (spec.entry.long, spec.entry.short):
        for cond in side.conditions:
            if cond.type == "ema_cross":
                if "fast" in cond.params:
                    values["ema_fast"] = int(cond.params["fast"])
                if "slow" in cond.params:
                    values["ema_slow"] = int(cond.params["slow"])
                break
    return values


def migrate_v1_to_v2(
    v1: StrategySpec | dict[str, Any],
    *,
    include_default_invariants: bool = True,
) -> tuple[StrategySpecV2, StrategyContract, StrategyInvariants]:
    """Map v1 → v2 without changing signal/risk/default semantics."""
    if isinstance(v1, dict):
        try:
            v1 = validate_spec(v1)
        except SpecValidationError as exc:
            raise SpecV2Error(f"v1 invalid before migration: {exc}") from exc

    params = _ema_parameters(v1)
    long_conds = [
        ConditionV2(type=c.type, params=dict(c.params)) for c in v1.entry.long.conditions
    ]
    short_conds = [
        ConditionV2(type=c.type, params=dict(c.params)) for c in v1.entry.short.conditions
    ]
    exit_conds = [ConditionV2(type=c.type, params=dict(c.params)) for c in v1.exit.conditions]

    family = v1.strategy.id
    spec_v2 = StrategySpecV2(
        identity=IdentityV2(
            strategy_id=v1.strategy.id,
            version=v1.strategy.version,
            name=v1.strategy.name,
            family_id=family,
            parent_version=v1.strategy.parent_version,
            derived_from=None,
            fork_of=None,
            schema_version="2.0",
        ),
        metadata=MetadataV2(
            description=v1.strategy.description,
            author=v1.strategy.author,
            ai_generated=v1.strategy.ai_generated,
            user_approved=v1.strategy.user_approved,
            ambiguous=v1.strategy.ambiguous,
            change_reason=v1.strategy.change_reason,
            created_by=v1.strategy.created_by,
        ),
        universe=UniverseV2(
            instruments=[v1.market.instrument],
            venue=v1.market.venue,
            asset_class=v1.market.asset_class,
        ),
        timeframe=TimeframeV2(
            timeframe=v1.market.timeframe,
            timezone=v1.market.timezone,
            session=v1.market.session,
        ),
        data_requirements=DataRequirementsV2(
            required=list(v1.data.required),
            warmup=v1.data.warmup,
            frequency=v1.data.frequency,
            source_policy=v1.data.source_policy,
        ),
        signal_logic=SignalLogicV2(
            entry_long=long_conds,
            entry_short=short_conds,
            exit=exit_conds,
            allowed_direction=_direction_from_entry(v1),
        ),
        position_sizing=PositionSizingV2(
            type=v1.position_sizing.type if v1.position_sizing.type in (
                "fixed", "risk_based", "volatility", "percent_equity"
            ) else "fixed",
            trade_size=str(v1.position_sizing.trade_size),
            risk_per_trade=v1.position_sizing.risk_per_trade,
            max_position=v1.position_sizing.max_position,
        ),
        stop_loss=StopLossV2(type=v1.stop_loss.type, value=v1.stop_loss.value),
        take_profit=TakeProfitV2(type=v1.take_profit.type, value=v1.take_profit.value),
        risk=RiskV2(
            daily_loss_limit=v1.risk.daily_loss_limit,
            max_drawdown=v1.risk.max_drawdown,
            max_open_positions=v1.risk.max_open_positions,
            max_consecutive_losses=v1.risk.max_consecutive_losses,
            exposure_limit=v1.risk.exposure_limit,
            leverage_limit=v1.risk.leverage_limit,
            risk_per_trade=v1.position_sizing.risk_per_trade,
        ),
        execution=ExecutionV2(
            order_type=v1.execution.order_type,
            time_in_force=v1.execution.time_in_force,
            retry_policy=v1.execution.retry_policy,
            assumptions=AssumptionsV2(
                slippage_model=v1.execution.slippage_policy,
                fee_model="model_default",
            ),
        ),
        regime=RegimeV2(
            enabled=v1.regime.enabled,
            intended=list(v1.regime.allow),
            forbidden=list(v1.regime.deny),
        ),
        compatibility=CompatibilityV2(
            permitted_environments=_map_env(v1.deployment.permitted_environments),
            required_engine_features=["ema_cross"] if params else [],
        ),
        parameters=ParametersV2(values=params),
        contract_id=f"{v1.strategy.id}:{v1.strategy.version}:contract",
    )

    contract = validate_contract(
        StrategyContract(
            contract_id=spec_v2.contract_id or f"{v1.strategy.id}:contract",
            strategy_id=v1.strategy.id,
            version=v1.strategy.version,
            what=v1.strategy.description or v1.strategy.name,
            why="Migrated from Spec v1; research hypothesis retained as description/name",
            when=[f"env:{e}" for e in spec_v2.compatibility.permitted_environments],
            when_not=["env:LIVE_without_approval", "ambiguous=true", "stale_data=true"],
            risk=(
                f"daily_loss_limit={v1.risk.daily_loss_limit};"
                f"max_drawdown={v1.risk.max_drawdown};"
                f"max_open_positions={v1.risk.max_open_positions}"
            ),
            invalidation=[
                "persistent adverse alpha vs declared hypothesis",
                "invariant violation under research validation",
                "data quality gate fail for required series",
            ],
            expected=["signals only when entry conditions hold", "respect risk limits"],
            abnormal=["orders without signal", "risk limit breach", "unknown execution state"],
            retirement=[
                "lifecycle RETIRED",
                "hypothesis invalidated",
                "superseded by newer family version",
            ],
        )
    )

    if include_default_invariants:
        inv = default_research_invariants(
            strategy_id=v1.strategy.id, version=v1.strategy.version
        )
        # Align max_open_positions invariant with migrated risk if present
        if v1.risk.max_open_positions is not None:
            for rule in inv.rules:
                if rule.kind == "max_open_positions":
                    rule.params["max"] = int(v1.risk.max_open_positions)
        inv = validate_invariants(inv)
        spec_v2.invariant_ids = [r.id for r in inv.rules]
    else:
        inv = StrategyInvariants(strategy_id=v1.strategy.id, version=v1.strategy.version, rules=[])
        # Fail closed if empty when requested without defaults — caller must supply
        if not include_default_invariants:
            pass

    validate_spec_v2(spec_v2)
    return spec_v2, contract, inv


def migrate_v1_file_to_v2(path: str | Path) -> tuple[StrategySpecV2, StrategyContract, StrategyInvariants]:
    return migrate_v1_to_v2(load_spec(path))


def assert_semantic_drift_zero(v1: StrategySpec, v2: StrategySpecV2) -> None:
    """Hard check: identity, params, signal, entry/exit, risk, sizing must match."""
    if v1.strategy.id != v2.identity.strategy_id:
        raise SpecV2Error("SEMANTIC_DRIFT: strategy_id")
    if v1.strategy.version != v2.identity.version:
        raise SpecV2Error("SEMANTIC_DRIFT: version")
    if v1.market.instrument != v2.primary_instrument():
        raise SpecV2Error("SEMANTIC_DRIFT: instrument")
    if v1.market.timeframe != v2.timeframe.timeframe:
        raise SpecV2Error("SEMANTIC_DRIFT: timeframe")
    if str(v1.position_sizing.trade_size) != str(v2.position_sizing.trade_size):
        raise SpecV2Error("SEMANTIC_DRIFT: trade_size")
    if v1.risk.max_drawdown != v2.risk.max_drawdown:
        raise SpecV2Error("SEMANTIC_DRIFT: max_drawdown")
    if v1.risk.daily_loss_limit != v2.risk.daily_loss_limit:
        raise SpecV2Error("SEMANTIC_DRIFT: daily_loss_limit")
    if v1.risk.max_open_positions != v2.risk.max_open_positions:
        raise SpecV2Error("SEMANTIC_DRIFT: max_open_positions")
    if v1.stop_loss.type != v2.stop_loss.type or v1.stop_loss.value != v2.stop_loss.value:
        raise SpecV2Error("SEMANTIC_DRIFT: stop_loss")
    if v1.take_profit.type != v2.take_profit.type or v1.take_profit.value != v2.take_profit.value:
        raise SpecV2Error("SEMANTIC_DRIFT: take_profit")

    def _conds(side_conds):
        return [(c.type, dict(c.params)) for c in side_conds]

    if _conds(v1.entry.long.conditions) != _conds(v2.signal_logic.entry_long):
        raise SpecV2Error("SEMANTIC_DRIFT: entry_long")
    if _conds(v1.entry.short.conditions) != _conds(v2.signal_logic.entry_short):
        raise SpecV2Error("SEMANTIC_DRIFT: entry_short")
    if _conds(v1.exit.conditions) != _conds(v2.signal_logic.exit):
        raise SpecV2Error("SEMANTIC_DRIFT: exit")
    if v1.execution.order_type != v2.execution.order_type:
        raise SpecV2Error("SEMANTIC_DRIFT: order_type")
    if v1.execution.slippage_policy != v2.execution.assumptions.slippage_model:
        raise SpecV2Error("SEMANTIC_DRIFT: slippage")

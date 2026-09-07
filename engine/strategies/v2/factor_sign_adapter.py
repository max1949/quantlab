"""Factor-sign Spec → Paper runtime contract (QLN-11 precondition).

Compiles already-declared Spec v2 factor_sign semantics into a PaperRuntimeContract.
Does NOT invent entry/exit; does NOT mutate params; does NOT use Factor Lab as Paper.
Fail closed on unsupported / ambiguous Specs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from engine.cost_model import CostConfig
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.spec_v2 import StrategySpecV2, validate_spec_v2

ADAPTER_VERSION = "factor_sign_paper_adapter_v1"
GENERATOR = "spec_compiler_factor_sign_v1"
BACKTEST_EXEC_SOURCE = "engine.backtest.signal_to_positions"


def _is_factor_sign(spec: StrategySpecV2) -> bool:
    types = {c.type for c in list(spec.signal_logic.entry_long) + list(spec.signal_logic.entry_short) + list(spec.signal_logic.exit)}
    if "factor_sign" in types or "factor_sign_flat_or_flip" in types:
        return True
    feat = set(spec.compatibility.required_engine_features or [])
    return "factor_sign" in feat


def _template_and_params(spec: StrategySpecV2) -> tuple[str, dict[str, Any]]:
    vals = dict(spec.parameters.values or {})
    tt = vals.get("template_type")
    window = vals.get("param_window", vals.get("window"))
    # Prefer explicit condition params if present
    for cond in list(spec.signal_logic.entry_long) + list(spec.signal_logic.entry_short):
        if cond.type == "factor_sign" and isinstance(cond.params, dict):
            tt = tt or cond.params.get("template_type")
            inner = cond.params.get("params") if isinstance(cond.params.get("params"), dict) else {}
            if window is None and "window" in inner:
                window = inner["window"]
    if not tt:
        raise SpecV2Error("factor_sign Spec missing template_type (no hidden default)")
    if window is None:
        raise SpecV2Error("factor_sign Spec missing window parameter (no hidden default)")
    return str(tt), {"window": int(window)}


@dataclass(frozen=True)
class FactorSignPaperContract:
    """Canonical PaperRuntimeContract payload for factor_sign strategies."""

    strategy_id: str
    strategy_version: str
    strategy_spec_hash: str
    adapter_version: str
    generator_version: str
    template_type: str
    factor_params: dict[str, Any]
    instrument: str
    timeframe: str
    trade_size: str
    allowed_direction: str
    max_open_positions: int | None
    fee_rate: float
    slippage_bps: float
    cost_source: str
    execution_rule: str
    lag_rule: str
    stop_loss_type: str
    take_profit_type: str
    permitted_environments: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_factor_sign_to_paper(
    spec: StrategySpecV2 | dict[str, Any],
    *,
    instrument: str | None = None,
) -> FactorSignPaperContract:
    """Compile Spec v2 factor_sign → Paper contract. Fail closed if unsupported."""
    spec = validate_spec_v2(spec)
    if spec.metadata.ambiguous:
        raise SpecV2Error("cannot compile ambiguous strategy")
    if "LIVE" in (spec.compatibility.permitted_environments or []):
        raise SpecV2Error("compiler refuses LIVE-capable specs")
    if not _is_factor_sign(spec):
        raise SpecV2Error("factor_sign adapter: Spec is not factor_sign (fail closed)")

    # Reject EMA-only specs here (wrong adapter)
    for cond in list(spec.signal_logic.entry_long) + list(spec.signal_logic.entry_short):
        if cond.type == "ema_cross":
            raise SpecV2Error("factor_sign adapter refuses ema_cross Specs")

    tt, params = _template_and_params(spec)
    univ = [str(x).upper() for x in spec.universe.instruments]
    if instrument is not None:
        inst = str(instrument).upper()
        if inst not in univ:
            raise SpecV2Error(f"instrument {inst} not in Spec universe {univ}")
    else:
        inst = univ[0] if univ else ""
    if not inst:
        raise SpecV2Error("factor_sign Spec missing primary instrument")

    vals = dict(spec.parameters.values or {})
    if vals.get("execution_rule") not in (None, "sign(signal)"):
        raise SpecV2Error(f"unsupported execution_rule: {vals.get('execution_rule')}")

    # Costs: explicit Spec params, else platform CostConfig when execution source is engine.backtest
    if vals.get("fee_rate") is not None and vals.get("slippage_bps") is not None:
        fee_rate = float(vals["fee_rate"])
        slippage_bps = float(vals["slippage_bps"])
        cost_source = "spec.parameters.values"
    elif str(vals.get("execution_rule_source") or "") == BACKTEST_EXEC_SOURCE:
        cfg = CostConfig()
        fee_rate = float(cfg.fee_rate)
        slippage_bps = float(cfg.slippage_bps)
        cost_source = "engine.cost_model.CostConfig (bound via execution_rule_source)"
    else:
        raise SpecV2Error(
            "factor_sign adapter: fee_rate/slippage_bps required when execution_rule_source "
            f"!= {BACKTEST_EXEC_SOURCE} (no hidden cost defaults)"
        )

    trade_size = spec.position_sizing.trade_size
    if trade_size is None or str(trade_size).strip() == "":
        raise SpecV2Error("factor_sign Spec missing position_sizing.trade_size (no hidden default)")

    if str(spec.stop_loss.type) != "none":
        raise SpecV2Error(f"factor_sign paper adapter unsupported stop_loss.type={spec.stop_loss.type}")

    lag = str(spec.execution.assumptions.latency_assumption or "")
    if lag and lag != "signal_t_affects_position_t_plus_1":
        raise SpecV2Error(f"unsupported latency_assumption: {lag}")

    return FactorSignPaperContract(
        strategy_id=spec.identity.strategy_id,
        strategy_version=spec.identity.version,
        strategy_spec_hash=spec.content_hash(),
        adapter_version=ADAPTER_VERSION,
        generator_version=GENERATOR,
        template_type=tt,
        factor_params=dict(params),
        instrument=inst,
        timeframe=str(spec.timeframe.timeframe),
        trade_size=str(trade_size),
        allowed_direction=str(spec.signal_logic.allowed_direction),
        max_open_positions=spec.risk.max_open_positions,
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        cost_source=cost_source,
        execution_rule="sign(signal)",
        lag_rule="signal_t_affects_position_t_plus_1",
        stop_loss_type=str(spec.stop_loss.type),
        take_profit_type=str(spec.take_profit.type),
        permitted_environments=list(spec.compatibility.permitted_environments or []),
    )

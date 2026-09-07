"""Nautilus Adapter Compiler — Spec v2 → QuantLab domain adapter → Nautilus params.

Does NOT import Nautilus strategy classes. Web/Product must not depend on Nautilus internals.
SPEC_TO_ADAPTER must be deterministic for same Spec + same Engine Adapter Version.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.spec_v2 import StrategySpecV2, extract_ema_params, validate_spec_v2

GENERATOR_VERSION_V2 = "spec_compiler_v2"
ENGINE_ADAPTER_VERSION = "quantlab_nautilus_adapter_v1"


@dataclass(frozen=True)
class CompiledAdapterArtifact:
    strategy_spec_hash: str
    generator_version: str
    engine_adapter_version: str
    kind: str
    template: str
    nautilus_params: dict[str, Any]
    source_spec_id: str
    source_spec_version: str
    domain_adapter: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _find_ema(spec: StrategySpecV2) -> bool:
    for cond in list(spec.signal_logic.entry_long) + list(spec.signal_logic.entry_short):
        if cond.type == "ema_cross":
            return True
    return "ema_fast" in spec.parameters.values


def compile_spec_v2(spec: StrategySpecV2 | dict[str, Any]) -> CompiledAdapterArtifact:
    spec = validate_spec_v2(spec)
    if spec.metadata.ambiguous:
        raise SpecV2Error("cannot compile ambiguous strategy")
    if "LIVE" in spec.compatibility.permitted_environments:
        raise SpecV2Error("compiler refuses LIVE-capable specs in QLN-2")

    if not _find_ema(spec):
        raise SpecV2Error(
            f"unsupported signal logic for {GENERATOR_VERSION_V2}; ema_cross required"
        )

    fast, slow = extract_ema_params(spec)
    if fast >= slow:
        raise SpecV2Error("ema fast must be < slow")

    domain_adapter = {
        "instrument": spec.primary_instrument(),
        "venue": spec.universe.venue,
        "timeframe": spec.timeframe.timeframe,
        "bar_type": spec.timeframe.bar_type,
        "fast_ema": fast,
        "slow_ema": slow,
        "trade_size": str(spec.position_sizing.trade_size),
        "order_type": spec.execution.order_type,
        "time_in_force": spec.execution.time_in_force,
        "allowed_direction": spec.signal_logic.allowed_direction,
        "warmup": spec.data_requirements.warmup,
        "slippage_model": spec.execution.assumptions.slippage_model,
        "fee_model": spec.execution.assumptions.fee_model,
        "max_open_positions": spec.risk.max_open_positions,
        "stop_loss": {"type": spec.stop_loss.type, "value": spec.stop_loss.value},
        "take_profit": {"type": spec.take_profit.type, "value": spec.take_profit.value},
    }

    # Nautilus-oriented params — plain dict, no Nautilus class names as business identity
    nautilus_params = {
        "instrument": domain_adapter["instrument"],
        "venue": domain_adapter["venue"],
        "timeframe": domain_adapter["timeframe"],
        "fast_ema": fast,
        "slow_ema": slow,
        "trade_size": domain_adapter["trade_size"],
        "bar_aggregation": "EXTERNAL",
    }

    return CompiledAdapterArtifact(
        strategy_spec_hash=spec.content_hash(),
        generator_version=GENERATOR_VERSION_V2,
        engine_adapter_version=ENGINE_ADAPTER_VERSION,
        kind="SPEC_COMPILED_STRATEGY",
        template="ema_cross",
        nautilus_params=nautilus_params,
        source_spec_id=spec.identity.strategy_id,
        source_spec_version=spec.identity.version,
        domain_adapter=domain_adapter,
    )


def compile_spec_v2_deterministic(spec: StrategySpecV2 | dict[str, Any]) -> dict[str, Any]:
    """Stable dict for golden tests — no timestamps / nautilus runtime version."""
    return compile_spec_v2(spec).to_dict()

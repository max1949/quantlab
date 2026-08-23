"""Compile Strategy Specification → deterministic Nautilus-oriented artifact.

Prefer template/DSL compiler over free-form LLM Python.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.nautilus.availability import nautilus_version
from engine.strategies.spec import StrategySpec
from engine.strategies.validate import SpecValidationError, validate_spec

GENERATOR_VERSION = "spec_compiler_v1"


@dataclass(frozen=True)
class CompiledStrategy:
    strategy_spec_hash: str
    generator_version: str
    nautilus_version: str | None
    generated_at: str
    kind: str  # SPEC_COMPILED_STRATEGY | CUSTOM_STRATEGY
    template: str
    nautilus_params: dict[str, Any]
    source_spec_id: str
    source_spec_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _find_condition(spec: StrategySpec, ctype: str) -> dict[str, Any] | None:
    for side in (spec.entry.long, spec.entry.short):
        for cond in side.conditions:
            if cond.type == ctype:
                return cond.params
    return None


def compile_spec(spec: StrategySpec | dict[str, Any]) -> CompiledStrategy:
    if isinstance(spec, dict):
        spec = validate_spec(spec)
    if spec.strategy.ambiguous:
        raise SpecValidationError("cannot compile ambiguous strategy (AMBIGUOUS=TRUE)")
    if spec.strategy.deployable or "LIVE" in spec.deployment.permitted_environments:
        raise SpecValidationError("compiler refuses LIVE/deployable specs in Phase 2/3")

    ema_params = _find_condition(spec, "ema_cross")
    if ema_params is not None:
        template = "ema_cross"
        nautilus_params = {
            "instrument": spec.market.instrument,
            "venue": spec.market.venue,
            "timeframe": spec.market.timeframe,
            "fast_ema": int(ema_params.get("fast", 10)),
            "slow_ema": int(ema_params.get("slow", 20)),
            "trade_size": str(spec.position_sizing.trade_size),
            "bar_aggregation": "EXTERNAL",
        }
    else:
        raise SpecValidationError(
            f"unsupported entry conditions for compiler {GENERATOR_VERSION}; "
            "Phase 2 supports ema_cross only"
        )

    return CompiledStrategy(
        strategy_spec_hash=spec.content_hash(),
        generator_version=GENERATOR_VERSION,
        nautilus_version=nautilus_version(),
        generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        kind="SPEC_COMPILED_STRATEGY",
        template=template,
        nautilus_params=nautilus_params,
        source_spec_id=spec.strategy.id,
        source_spec_version=spec.strategy.version,
    )


def compile_deterministic(spec: StrategySpec | dict[str, Any]) -> dict[str, Any]:
    """Stable dict for golden tests (excludes generated_at)."""
    compiled = compile_spec(spec)
    data = compiled.to_dict()
    data.pop("generated_at", None)
    return data


def write_compiled(compiled: CompiledStrategy, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(compiled.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return p

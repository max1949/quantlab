"""Strategy Spec → shared Nautilus runtime parameters (Backtest + Paper SSOT)."""

from __future__ import annotations

import re
from typing import Any

from engine.strategies.compiler import compile_spec
from engine.strategies.spec import StrategySpec
from engine.strategies.validate import SpecValidationError, validate_spec


class RuntimeParamsError(SpecValidationError):
    """Spec cannot produce runtime params — no silent fallback."""


_TIMEFRAME_RE = re.compile(r"^(\d+)(m|h|d)$", re.I)


def parse_timeframe_minutes(timeframe: str) -> int:
    raw = (timeframe or "").strip().lower()
    m = _TIMEFRAME_RE.match(raw)
    if not m:
        raise RuntimeParamsError(f"无效 timeframe: {timeframe!r}（需要如 1m/15m/1h）")
    n, unit = int(m.group(1)), m.group(2).lower()
    if unit == "m":
        return n
    if unit == "h":
        return n * 60
    if unit == "d":
        return n * 60 * 24
    raise RuntimeParamsError(f"unsupported timeframe unit: {unit}")


def require_nautilus_runtime_params(spec: StrategySpec | dict[str, Any]) -> dict[str, Any]:
    """Compile spec and return params used identically by backtest + paper runners."""
    if isinstance(spec, dict):
        spec = validate_spec(spec)
    compiled = compile_spec(spec)
    p = dict(compiled.nautilus_params)

    for key in ("fast_ema", "slow_ema", "trade_size", "instrument", "timeframe"):
        if key not in p or p[key] in (None, ""):
            raise RuntimeParamsError(f"Strategy Spec 缺少编译参数: {key}")

    fast = int(p["fast_ema"])
    slow = int(p["slow_ema"])
    if fast >= slow:
        raise RuntimeParamsError(f"EMA fast ({fast}) 必须小于 slow ({slow})")

    instrument = str(p["instrument"]).upper().replace("/", "")
    bar_minutes = parse_timeframe_minutes(str(p["timeframe"]))

    return {
        "ema_fast": fast,
        "ema_slow": slow,
        "trade_size": str(p["trade_size"]),
        "instrument": instrument,
        "bar_minutes": bar_minutes,
        "timeframe": str(p["timeframe"]),
        "venue": str(p.get("venue") or "BINANCE"),
        "template": compiled.template,
        "compiled_hash": compiled.strategy_spec_hash,
        "strategy_spec_id": compiled.source_spec_id,
        "strategy_spec_version": compiled.source_spec_version,
    }


def runtime_params_from_effective_config(effective: dict[str, Any]) -> dict[str, Any]:
    """Load frozen runtime params from PaperRun.effective_config (no hardcoded overrides)."""
    if not effective:
        raise RuntimeParamsError("effective_config 为空")
    if isinstance(effective.get("spec"), dict):
        return require_nautilus_runtime_params(effective["spec"])
    for key in ("ema_fast", "ema_slow", "trade_size", "instrument", "bar_minutes"):
        if key not in effective or effective[key] in (None, ""):
            raise RuntimeParamsError(f"effective_config 缺少 Strategy Spec 参数: {key}")
    return {
        "ema_fast": int(effective["ema_fast"]),
        "ema_slow": int(effective["ema_slow"]),
        "trade_size": str(effective["trade_size"]),
        "instrument": str(effective["instrument"]).upper().replace("/", ""),
        "bar_minutes": int(effective["bar_minutes"]),
        "timeframe": str(effective.get("timeframe") or f"{effective['bar_minutes']}m"),
        "venue": str(effective.get("venue") or "BINANCE"),
        "template": str(effective.get("template") or "ema_cross"),
        "compiled_hash": str(effective.get("compiled_hash") or ""),
        "strategy_spec_id": str(effective.get("strategy_spec_id") or ""),
        "strategy_spec_version": str(effective.get("strategy_spec_version") or ""),
    }

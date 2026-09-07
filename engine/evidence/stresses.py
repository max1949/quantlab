"""Fee / slippage / regime / extreme stress tests for Evidence Pipeline."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd

from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.evidence.thresholds import EVIDENCE_THRESHOLDS

SignalFn = Callable[[pd.DataFrame], pd.Series]


def fee_stress(compute: SignalFn, ohlcv: pd.DataFrame) -> dict[str, Any]:
    thr = EVIDENCE_THRESHOLDS
    base = CostConfig()
    mult = float(thr["fee_stress_mult"])
    base_m = run_backtest(compute(ohlcv), ohlcv, base)["metrics"]
    stressed = CostConfig(fee_rate=base.fee_rate * mult, slippage_bps=base.slippage_bps)
    stress_m = run_backtest(compute(ohlcv), ohlcv, stressed)["metrics"]
    base_s = base_m.get("sharpe")
    stress_s = stress_m.get("sharpe")
    status = "PASS"
    if base_s is None or float(base_s) <= float(thr["stress_min_sharpe"]):
        status = "FAIL"
    elif stress_s is None or float(stress_s) <= float(thr["stress_min_sharpe"]):
        status = "FAIL"
    return {
        "status": status,
        "multiplier": mult,
        "base": base_m,
        "stressed": stress_m,
    }


def slippage_stress(compute: SignalFn, ohlcv: pd.DataFrame) -> dict[str, Any]:
    thr = EVIDENCE_THRESHOLDS
    base = CostConfig()
    mult = float(thr["slippage_stress_mult"])
    base_m = run_backtest(compute(ohlcv), ohlcv, base)["metrics"]
    stressed = CostConfig(fee_rate=base.fee_rate, slippage_bps=base.slippage_bps * mult)
    stress_m = run_backtest(compute(ohlcv), ohlcv, stressed)["metrics"]
    base_s = base_m.get("sharpe")
    stress_s = stress_m.get("sharpe")
    status = "PASS"
    if base_s is None or float(base_s) <= float(thr["stress_min_sharpe"]):
        status = "FAIL"
    elif stress_s is None or float(stress_s) <= float(thr["stress_min_sharpe"]):
        status = "FAIL"
    return {
        "status": status,
        "multiplier": mult,
        "base": base_m,
        "stressed": stress_m,
    }


def regime_split_test(compute: SignalFn, ohlcv: pd.DataFrame) -> dict[str, Any]:
    """Split by realized volatility regime (low/high) — not fake labels."""
    thr = EVIDENCE_THRESHOLDS
    close = ohlcv["close"].astype(float)
    vol = close.pct_change().rolling(20).std()
    med = float(vol.median()) if vol.notna().any() else 0.0
    low = ohlcv[vol <= med]
    high = ohlcv[vol > med]
    rows: dict[str, Any] = {}
    sharpes: list[float] = []
    for label, part in (("low_vol", low), ("high_vol", high)):
        if len(part) < 30:
            rows[label] = {"status": "INSUFFICIENT", "bars": int(len(part))}
            continue
        m = run_backtest(compute(part), part, CostConfig())["metrics"]
        rows[label] = m
        if m.get("sharpe") is not None:
            sharpes.append(float(m["sharpe"]))
    positive = sum(1 for s in sharpes if s > 0)
    ratio = (positive / len(sharpes)) if sharpes else None
    if ratio is None:
        status = "INSUFFICIENT"
    elif ratio < float(thr["regime_min_positive_ratio"]):
        status = "FAIL"
    else:
        status = "PASS"
    return {"status": status, "positive_ratio": ratio, "regimes": rows}


def extreme_period_test(compute: SignalFn, ohlcv: pd.DataFrame) -> dict[str, Any]:
    """Worst rolling window by cumulative return — pre-declared drawdown ceiling."""
    thr = EVIDENCE_THRESHOLDS
    close = ohlcv["close"].astype(float)
    ret = close.pct_change().fillna(0.0)
    window = min(60, max(20, len(ohlcv) // 5))
    roll = ret.rolling(window).sum()
    if roll.isna().all():
        return {"status": "INSUFFICIENT", "reason": "no_window"}
    worst_end = int(roll.idxmin() and roll.index.get_loc(roll.idxmin()))
    # Use integer location safely
    try:
        loc = roll.index.get_loc(roll.idxmin())
        if isinstance(loc, slice):
            end = loc.stop - 1
        elif isinstance(loc, np.ndarray):
            end = int(np.where(loc)[0][0])
        else:
            end = int(loc)
    except Exception:  # noqa: BLE001
        end = int(np.nanargmin(roll.to_numpy()))
    start = max(0, end - window + 1)
    part = ohlcv.iloc[start : end + 1]
    if len(part) < 10:
        return {"status": "INSUFFICIENT", "reason": "short_extreme_window"}
    m = run_backtest(compute(part), part, CostConfig())["metrics"]
    dd = abs(float(m.get("max_drawdown") or 0.0))
    status = "FAIL" if dd > float(thr["extreme_max_drawdown"]) else "PASS"
    return {
        "status": status,
        "window": window,
        "start": str(part.index[0]),
        "end": str(part.index[-1]),
        "metrics": m,
        "max_drawdown": dd,
    }

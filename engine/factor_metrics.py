"""因子评价指标 (IC / 综合评分) — 纯函数, 不依赖 DB。"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


IC_HORIZON_BY_TF = {
    "1m": 5,
    "5m": 3,
    "15m": 2,
    "30m": 2,
    "1h": 1,
    "1d": 1,
}


def _f(x) -> float | None:
    if x is None:
        return None
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(xf) or math.isinf(xf):
        return None
    return xf


def forward_returns(close: pd.Series, horizon: int = 1) -> pd.Series:
    return close.pct_change(horizon).shift(-horizon)


def _rank_corr(a: pd.Series, b: pd.Series) -> float | None:
  ar = a.rank()
  br = b.rank()
  return _f(ar.corr(br))


def factor_ic(
    factor: pd.Series,
    close: pd.Series,
    horizon: int = 1,
    method: str = "spearman",
) -> dict:
    """因子与未来收益的 IC (整体 + 滚动均值)。"""
    fwd = forward_returns(close, horizon)
    aligned = pd.concat([factor.rename("f"), fwd.rename("r")], axis=1).dropna()
    if len(aligned) < 30:
        return {
            "ic_mean": None,
            "ic_std": None,
            "ic_ir": None,
            "rank_ic_mean": None,
            "n_obs": int(len(aligned)),
        }

    if method == "pearson":
        overall = aligned["f"].corr(aligned["r"])
        rank_overall = _rank_corr(aligned["f"], aligned["r"])
    else:
        overall = _rank_corr(aligned["f"], aligned["r"])
        rank_overall = overall

    ic_mean = _f(overall)
    ic_std = None
    ic_ir = None

    return {
        "ic_mean": ic_mean,
        "ic_std": ic_std,
        "ic_ir": ic_ir,
        "rank_ic_mean": _f(rank_overall),
        "n_obs": int(len(aligned)),
    }


def composite_factor_score(
    *,
    sharpe: float | None,
    oos_sharpe: float | None,
    ic_mean: float | None,
    turnover: float | None,
    robustness: float | None = None,
) -> float | None:
    """0~100 综合分, 用于参数扫描排序。"""
    parts: list[float] = []
    weights: list[float] = []

    if sharpe is not None:
        parts.append(_clamp(sharpe / 2.0))
        weights.append(0.30)
    if oos_sharpe is not None:
        parts.append(_clamp(oos_sharpe / 1.5))
        weights.append(0.30)
    if ic_mean is not None:
        parts.append(_clamp(abs(ic_mean) / 0.08))
        weights.append(0.20)
    if turnover is not None:
        parts.append(_clamp(1.0 - min(abs(turnover) / 80.0, 1.0)))
        weights.append(0.10)
    if robustness is not None:
        parts.append(_clamp(robustness / 100.0))
        weights.append(0.10)

    if not parts:
        return None
    wsum = sum(weights)
    score = sum(p * w for p, w in zip(parts, weights)) / wsum
    return round(score * 100.0, 1)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

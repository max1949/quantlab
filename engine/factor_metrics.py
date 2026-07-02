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
    return close.pct_change(horizon, fill_method=None).shift(-horizon)


def _rank_corr(a: pd.Series, b: pd.Series) -> float | None:
  ar = a.rank()
  br = b.rank()
  return _f(ar.corr(br))


def _series_ic(a: pd.Series, b: pd.Series, method: str) -> float | None:
    if method == "pearson":
        return _f(a.corr(b))
    return _rank_corr(a, b)


def _bucket_ic_series(
    aligned: pd.DataFrame,
    method: str,
    *,
    min_per_bucket: int = 5,
    max_points: int = 120,
) -> list[dict]:
    """按日/周 (或等长分块) 计算 IC 序列, 供前端展示稳定性。"""
    points: list[dict] = []
    if isinstance(aligned.index, pd.DatetimeIndex) and aligned.index.nunique() > 1:
        bars_per_day = len(aligned) / max(1, aligned.index.normalize().nunique())
        if bars_per_day >= 2:
            grouped = aligned.groupby(aligned.index.floor("D"))
            date_fmt = lambda dt: pd.Timestamp(dt).strftime("%Y-%m-%d")  # noqa: E731
            bucket_min = min_per_bucket
        else:
            grouped = aligned.groupby(aligned.index.to_period("W"))
            date_fmt = lambda dt: str(dt)  # noqa: E731
            bucket_min = max(3, min_per_bucket - 2)
        for dt, g in grouped:
            if len(g) < bucket_min:
                continue
            ic_val = _series_ic(g["f"], g["r"], method)
            if ic_val is not None:
                points.append({"date": date_fmt(dt), "ic": ic_val})
    elif len(aligned) >= min_per_bucket * 4:
        chunk = max(min_per_bucket * 3, len(aligned) // 40)
        for i in range(0, len(aligned) - chunk + 1, chunk):
            g = aligned.iloc[i : i + chunk]
            if len(g) < min_per_bucket:
                continue
            ic_val = _series_ic(g["f"], g["r"], method)
            if ic_val is not None:
                points.append({"date": str(i), "ic": ic_val})

    if len(points) > max_points:
        step = max(1, len(points) // max_points)
        points = points[::step][-max_points:]
    return points


def factor_ic(
    factor: pd.Series,
    close: pd.Series,
    horizon: int = 1,
    method: str = "spearman",
    max_series_points: int = 120,
) -> dict:
    """因子与未来收益的 IC (全样本 + 分桶序列 + IC_IR)。"""
    fwd = forward_returns(close, horizon)
    aligned = pd.concat([factor.rename("f"), fwd.rename("r")], axis=1).dropna()
    if len(aligned) < 30:
        return {
            "ic_mean": None,
            "ic_std": None,
            "ic_ir": None,
            "rank_ic_mean": None,
            "ic_series": [],
            "n_obs": int(len(aligned)),
        }

    if method == "pearson":
        overall = aligned["f"].corr(aligned["r"])
        rank_overall = _rank_corr(aligned["f"], aligned["r"])
    else:
        overall = _rank_corr(aligned["f"], aligned["r"])
        rank_overall = overall

    ic_mean = _f(overall)
    ic_series = _bucket_ic_series(
        aligned, method, max_points=max_series_points
    )
    series_vals = [p["ic"] for p in ic_series if p.get("ic") is not None]
    ic_std = None
    ic_ir = None
    if len(series_vals) >= 2:
        std = float(np.std(series_vals))
        ic_std = _f(std)
        if std > 0:
            ic_ir = _f(float(np.mean(series_vals)) / std)

    return {
        "ic_mean": ic_mean,
        "ic_std": ic_std,
        "ic_ir": ic_ir,
        "rank_ic_mean": _f(rank_overall),
        "ic_series": ic_series,
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

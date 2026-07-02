"""行情数据质量评估 — 缺口、涨跌停/停牌棒、零成交量等。"""

from __future__ import annotations

import math

import pandas as pd

TIMEFRAME_GAP_RULES: dict[str, tuple[str, float]] = {
    "1m": ("1min", 3.0),
    "5m": ("5min", 3.0),
    "15m": ("15min", 3.0),
    "30m": ("30min", 3.0),
    "1h": ("1h", 3.0),
    "1d": ("1D", 5.0),  # 日历日: 超过 5 天视为异常缺口
}


def _sorted_df(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        return df
    return df.sort_index()


def _large_gap_count(index: pd.DatetimeIndex, timeframe: str) -> int:
    if len(index) < 2:
        return 0
    rule, mult = TIMEFRAME_GAP_RULES.get(timeframe, ("1D", 5.0))
    deltas = index.to_series().diff().dropna()
    if timeframe == "1d":
        threshold = pd.Timedelta(days=mult)
    else:
        threshold = pd.Timedelta(rule) * mult
    return int((deltas > threshold).sum())


def _limit_lock_bars(df: pd.DataFrame) -> tuple[int, float]:
    needed = {"open", "high", "low", "close", "volume"}
    if not needed.issubset(df.columns) or len(df) < 20:
        return 0, 0.0
    close = df["close"].clip(lower=1e-6)
    flat = (df["high"] - df["low"]).abs() / close < 1e-6
    vol_med = df["volume"].rolling(20, min_periods=5).median()
    low_vol = df["volume"] < (vol_med * 0.1)
    locks = flat & low_vol.fillna(False)
    n = int(locks.sum())
    return n, n / len(df)


def _zero_volume_bars(df: pd.DataFrame) -> tuple[int, float]:
    if "volume" not in df.columns or len(df) == 0:
        return 0, 0.0
    n = int((df["volume"] <= 0).sum())
    return n, n / len(df)


def assess_ohlcv_quality(df: pd.DataFrame, timeframe: str = "1d") -> dict:
    """评估 OHLCV 是否适合因子研究 (纯函数)。"""
    warnings: list[str] = []
    df = _sorted_df(df)
    n = len(df)
    if n < 20:
        return {
            "passed": False,
            "grade": "不足",
            "warnings": ["数据量过少 (<20根)，统计不可靠"],
            "stats": {"rows": n},
        }

    gap_count = _large_gap_count(df.index, timeframe) if isinstance(df.index, pd.DatetimeIndex) else 0
    gap_ratio = gap_count / max(1, n - 1)
    lock_n, lock_ratio = _limit_lock_bars(df)
    zv_n, zv_ratio = _zero_volume_bars(df)
    dup = int(df.index.duplicated().sum()) if hasattr(df.index, "duplicated") else 0

    stats = {
        "rows": n,
        "large_gap_count": gap_count,
        "large_gap_ratio": round(gap_ratio, 4),
        "limit_lock_bars": lock_n,
        "limit_lock_ratio": round(lock_ratio, 4),
        "zero_volume_bars": zv_n,
        "zero_volume_ratio": round(zv_ratio, 4),
        "duplicate_timestamps": dup,
    }

    if gap_ratio > 0.05:
        warnings.append(f"时间缺口偏多 (约 {gap_ratio * 100:.1f}% 间隔异常，可能缺 bar)")
    if lock_ratio > 0.08:
        warnings.append(
            f"疑似涨跌停/停牌棒约 {lock_ratio * 100:.1f}% — 因子信号在该时段可能失真"
        )
    if zv_ratio > 0.02:
        warnings.append(f"零成交量 K 线占比 {zv_ratio * 100:.1f}%")
    if dup > 0:
        warnings.append(f"存在 {dup} 条重复时间戳")

    passed = len(warnings) == 0
    if passed:
        grade = "良好"
    elif len(warnings) <= 2:
        grade = "一般"
    else:
        grade = "留意"

    return {
        "passed": passed,
        "grade": grade,
        "warnings": warnings,
        "stats": stats,
    }

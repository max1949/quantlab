"""日盘/夜盘分段稳健性 — 检验中频因子是否依赖特定交易时段。"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from engine.backtest import run_backtest
from engine.cost_model import CostConfig

SignalFn = Callable[[pd.DataFrame], pd.Series]

INTRADAY_TIMEFRAMES = frozenset({"1m", "5m", "15m", "30m", "1h"})
MIN_SEGMENT_BARS = 40

SESSIONS: tuple[tuple[str, str], ...] = (
    ("day", "日盘"),
    ("night", "夜盘"),
)


def _session_mask(index: pd.DatetimeIndex, session: str) -> pd.Series:
    hours = index.hour
    if session == "day":
        return (hours >= 9) & (hours < 15)
    if session == "night":
        return (hours >= 21) | (hours < 3)
    return pd.Series(False, index=index)


def turnover_capacity_hint(turnover: float | None, timeframe: str = "1d") -> str | None:
    """根据回测换手率给出容量/成本提示 (粗估)。"""
    if turnover is None:
        return None
    t = abs(float(turnover))
    intraday = timeframe in INTRADAY_TIMEFRAMES
    if t > 80:
        return "换手率极高，即使小资金也可能被滑点严重侵蚀，实盘需大幅打折。"
    if t > 40:
        if intraday:
            return "中频换手偏高，对滑点与盘口深度敏感，建议拉长持仓或做成本敏感性分析。"
        return "换手率偏高，实盘成本可能明显低于回测，请做成本敏感性分析。"
    if intraday and t > 25:
        return "分钟级换手不低，扩容前请估算可承载资金规模。"
    return None


def evaluate_session_segments(
    compute_signal: SignalFn,
    ohlcv: pd.DataFrame,
    cost_config: CostConfig | None = None,
    timeframe: str = "1d",
) -> dict:
    """在日盘 / 夜盘子样本上分别回测，评估跨时段一致性。"""
    if timeframe not in INTRADAY_TIMEFRAMES:
        return {
            "skipped": True,
            "reason": "仅分钟/小时线支持日盘夜盘分段检验",
            "timeframe": timeframe,
        }
    if not isinstance(ohlcv.index, pd.DatetimeIndex):
        return {"skipped": True, "reason": "缺少时间索引", "timeframe": timeframe}

    cfg = cost_config or CostConfig()
    segments: list[dict] = []
    for key, label in SESSIONS:
        mask = _session_mask(ohlcv.index, key)
        slice_df = ohlcv.loc[mask]
        bars = int(len(slice_df))
        if bars < MIN_SEGMENT_BARS:
            segments.append(
                {"session": key, "label": label, "bars": bars, "skipped": True}
            )
            continue
        metrics = run_backtest(compute_signal(slice_df), slice_df, cfg)["metrics"]
        segments.append(
            {
                "session": key,
                "label": label,
                "bars": bars,
                "skipped": False,
                "metrics": metrics,
                "sharpe": metrics.get("sharpe"),
                "turnover": metrics.get("turnover"),
            }
        )

    active = [s for s in segments if not s.get("skipped")]
    sharpes = [float(s["sharpe"]) for s in active if s.get("sharpe") is not None]
    notes: list[str] = []
    if len(sharpes) >= 2:
        if sharpes[0] * sharpes[1] < 0:
            notes.append("日盘与夜盘夏普方向不一致，策略可能对交易时段敏感。")
        spread = abs(sharpes[0] - sharpes[1])
        if spread > 1.0:
            notes.append(f"日盘/夜盘夏普差距较大 (Δ≈{spread:.2f})，建议确认逻辑是否时段依赖。")
    elif len(active) == 1:
        notes.append("仅一段数据充足，无法对比日盘与夜盘。")

    positive_ratio = (
        float(np.mean([s > 0 for s in sharpes])) if sharpes else None
    )
    return {
        "skipped": len(active) == 0,
        "reason": None if active else "日盘/夜盘样本均不足",
        "timeframe": timeframe,
        "segments": segments,
        "summary": {
            "n_active": len(active),
            "mean_sharpe": float(np.mean(sharpes)) if sharpes else None,
            "positive_ratio": positive_ratio,
        },
        "notes": notes,
    }

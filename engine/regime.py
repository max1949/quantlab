"""市场状态识别 — 波动率分位制度 (机构风控基础)。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_vol_regime(
    ohlcv: pd.DataFrame,
    *,
    vol_window: int = 20,
    lookback: int = 252,
) -> dict:
    """基于滚动年化波动率历史分位的三档制度: low / mid / high。"""
    if "close" not in ohlcv.columns or len(ohlcv) < vol_window + 10:
        raise ValueError("行情不足，无法识别波动制度")
    close = ohlcv["close"].astype(float)
    rets = close.pct_change(fill_method=None).dropna()
    if rets.empty:
        raise ValueError("收益率序列为空")
    vol = rets.rolling(vol_window).std() * np.sqrt(252)
    vol = vol.dropna()
    if vol.empty:
        raise ValueError("波动率序列为空")
    tail = vol.tail(max(lookback, vol_window * 2))
    current = float(vol.iloc[-1])
    pct = float((tail < current).mean())
    if pct < 0.33:
        regime = "low"
        label = "低波动"
    elif pct > 0.66:
        regime = "high"
        label = "高波动"
    else:
        regime = "mid"
        label = "中等波动"
    return {
        "regime": regime,
        "label": label,
        "volatility_ann": round(current, 4),
        "percentile": round(pct, 3),
        "vol_window": vol_window,
        "as_of": str(vol.index[-1].date()) if hasattr(vol.index[-1], "date") else str(vol.index[-1]),
        "hint": _regime_hint(regime),
    }


def detect_regime_shift(
    ohlcv: pd.DataFrame,
    *,
    shift_bars: int = 20,
    vol_window: int = 20,
    lookback: int = 252,
) -> dict:
    """对比当前波动制度与 shift_bars 根 K 线前的制度, 用于主动提醒制度切换。"""
    min_len = vol_window + shift_bars + 10
    if "close" not in ohlcv.columns or len(ohlcv) < min_len:
        return {"shifted": False, "reason": "insufficient_data"}

    current = detect_vol_regime(ohlcv, vol_window=vol_window, lookback=lookback)
    prior_df = ohlcv.iloc[:-shift_bars]
    try:
        prior = detect_vol_regime(prior_df, vol_window=vol_window, lookback=lookback)
    except ValueError:
        return {"shifted": False, "reason": "insufficient_data"}

    shifted = prior["regime"] != current["regime"]
    return {
        "shifted": shifted,
        "from_regime": prior["regime"],
        "to_regime": current["regime"],
        "from_label": prior["label"],
        "to_label": current["label"],
        "shift_bars": shift_bars,
        "as_of": current["as_of"],
        "hint": _shift_hint(prior["regime"], current["regime"]) if shifted else "",
    }


def _shift_hint(from_regime: str, to_regime: str) -> str:
    if to_regime == "high":
        return "波动率抬升 — 趋势因子回撤风险上升, 建议重验或考虑均值回归类模板。"
    if to_regime == "low":
        return "波动率回落 — 突破动量信号可能偏弱, 关注制度适配与样本外表现。"
    if from_regime == "high" and to_regime == "mid":
        return "高波动缓和 — 可重新评估趋势类因子的风险收益比。"
    return "波动制度发生变化 — 建议对当前因子做样本外复检与制度适配检查。"


def _regime_hint(regime: str) -> str:
    if regime == "high":
        return "高波动制度：趋势/动量因子可能失效，注意回撤与成本；可考虑降低杠杆或换均值回归。"
    if regime == "low":
        return "低波动制度：突破策略信号偏弱，可关注波动率因子或耐心等待制度切换。"
    return "中等波动：常规模板因子可正常验证，仍建议做样本外与稳健性检查。"

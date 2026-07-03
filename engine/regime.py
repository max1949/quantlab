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


def _regime_hint(regime: str) -> str:
    if regime == "high":
        return "高波动制度：趋势/动量因子可能失效，注意回撤与成本；可考虑降低杠杆或换均值回归。"
    if regime == "low":
        return "低波动制度：突破策略信号偏弱，可关注波动率因子或耐心等待制度切换。"
    return "中等波动：常规模板因子可正常验证，仍建议做样本外与稳健性检查。"

"""Baseline Library — first Strategy Validation yardstick (not holy-grail hunt)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from engine.factor_engine import compute_template_factor

SignalFn = Callable[[pd.DataFrame], pd.Series]


def _ema_signal(ohlcv: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    close = ohlcv["close"].astype(float)
    return close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()


def _channel_breakout(ohlcv: pd.DataFrame, window: int = 20) -> pd.Series:
    high = ohlcv["high"].astype(float).rolling(window).max().shift(1)
    low = ohlcv["low"].astype(float).rolling(window).min().shift(1)
    close = ohlcv["close"].astype(float)
    up = (close > high).astype(float)
    down = (close < low).astype(float)
    return up - down


def _vol_breakout(ohlcv: pd.DataFrame, window: int = 20) -> pd.Series:
    vol = compute_template_factor(ohlcv, "volatility", {"window": window})
    mom = compute_template_factor(ohlcv, "momentum", {"window": max(5, window // 2)})
    thresh = vol.rolling(window).median()
    expand = (vol > thresh).astype(float)
    return expand * mom.fillna(0.0)


def _rsi_mr(ohlcv: pd.DataFrame, window: int = 14) -> pd.Series:
    r = compute_template_factor(ohlcv, "rsi", {"window": window})
    # Oversold → long, overbought → short (mean reversion)
    return (50.0 - r).fillna(0.0)


def _bollinger_mr(ohlcv: pd.DataFrame, window: int = 20) -> pd.Series:
    import numpy as np

    close = ohlcv["close"].astype(float)
    ma = close.rolling(window).mean()
    sd = close.rolling(window).std()
    z = (close - ma) / sd.replace(0.0, np.nan)
    return (-z).fillna(0.0)


@dataclass(frozen=True)
class BaselineCandidate:
    strategy_id: str
    strategy_version: str
    family: str  # trend | mean_reversion | momentum | volatility
    hypothesis: str
    market: str
    timeframe: str
    param_count: int
    base_params: dict
    neighborhood: list[dict]
    signal_factory: Callable[[dict], SignalFn]


def _ema_factory(params: dict) -> SignalFn:
    f, s = int(params["fast"]), int(params["slow"])
    return lambda df, ff=f, ss=s: _ema_signal(df, ff, ss)


def _tpl_factory(factor_type: str) -> Callable[[dict], SignalFn]:
    def make(params: dict) -> SignalFn:
        p = dict(params)
        return lambda df, pp=p: compute_template_factor(df, factor_type, pp)

    return make


def _channel_factory(params: dict) -> SignalFn:
    w = int(params["window"])
    return lambda df, ww=w: _channel_breakout(df, ww)


def _vol_factory(params: dict) -> SignalFn:
    w = int(params["window"])
    return lambda df, ww=w: _vol_breakout(df, ww)


def _rsi_factory(params: dict) -> SignalFn:
    w = int(params["window"])
    return lambda df, ww=w: _rsi_mr(df, ww)


def _bb_factory(params: dict) -> SignalFn:
    w = int(params["window"])
    return lambda df, ww=w: _bollinger_mr(df, ww)


def baseline_library() -> list[BaselineCandidate]:
    """Minimal yardstick set for batch 001."""
    ema_nb = [
        {"fast": 15, "slow": 40},
        {"fast": 15, "slow": 50},
        {"fast": 20, "slow": 40},
        {"fast": 20, "slow": 50},
        {"fast": 20, "slow": 60},
        {"fast": 25, "slow": 50},
        {"fast": 25, "slow": 60},
        {"fast": 10, "slow": 20},
    ]
    return [
        BaselineCandidate(
            strategy_id="baseline_ema_cross_trend",
            strategy_version="v1",
            family="trend",
            hypothesis="EMA fast/slow crossover captures short-horizon trend continuation.",
            market="EUR/USD",
            timeframe="15m",
            param_count=2,
            base_params={"fast": 20, "slow": 50},
            neighborhood=ema_nb,
            signal_factory=_ema_factory,
        ),
        BaselineCandidate(
            strategy_id="baseline_ema_cross_btc",
            strategy_version="v1",
            family="trend",
            hypothesis="Same EMA trend rule on BTCUSDT golden sample.",
            market="BTCUSDT",
            timeframe="15m",
            param_count=2,
            base_params={"fast": 10, "slow": 20},
            neighborhood=[
                {"fast": 8, "slow": 18},
                {"fast": 10, "slow": 20},
                {"fast": 12, "slow": 22},
                {"fast": 10, "slow": 24},
                {"fast": 14, "slow": 28},
            ],
            signal_factory=_ema_factory,
        ),
        BaselineCandidate(
            strategy_id="baseline_channel_breakout",
            strategy_version="v1",
            family="trend",
            hypothesis="Close break of prior N-bar high/low continues.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 20},
            neighborhood=[{"window": w} for w in (15, 18, 20, 22, 25, 30)],
            signal_factory=_channel_factory,
        ),
        BaselineCandidate(
            strategy_id="baseline_sma_ratio_trend",
            strategy_version="v1",
            family="trend",
            hypothesis="Price above/below SMA signals trend direction.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 20},
            neighborhood=[{"window": w} for w in (10, 15, 20, 25, 30, 40)],
            signal_factory=_tpl_factory("sma_ratio"),
        ),
        BaselineCandidate(
            strategy_id="baseline_rsi_mean_reversion",
            strategy_version="v1",
            family="mean_reversion",
            hypothesis="RSI extremes mean-revert over short horizons.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 14},
            neighborhood=[{"window": w} for w in (10, 12, 14, 16, 18, 21)],
            signal_factory=_rsi_factory,
        ),
        BaselineCandidate(
            strategy_id="baseline_bollinger_zscore",
            strategy_version="v1",
            family="mean_reversion",
            hypothesis="Price z-score vs rolling band mean-reverts.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 20},
            neighborhood=[{"window": w} for w in (15, 18, 20, 22, 25, 30)],
            signal_factory=_bb_factory,
        ),
        BaselineCandidate(
            strategy_id="baseline_mean_reversion_z",
            strategy_version="v1",
            family="mean_reversion",
            hypothesis="Negative z-score of price vs mean predicts reversion.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 20},
            neighborhood=[{"window": w} for w in (15, 18, 20, 22, 25, 30)],
            signal_factory=_tpl_factory("mean_reversion"),
        ),
        BaselineCandidate(
            strategy_id="baseline_ts_momentum",
            strategy_version="v1",
            family="momentum",
            hypothesis="Positive past N-bar return continues (time-series momentum).",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 20},
            neighborhood=[{"window": w} for w in (10, 15, 20, 25, 30, 40)],
            signal_factory=_tpl_factory("momentum"),
        ),
        BaselineCandidate(
            strategy_id="baseline_roc_momentum",
            strategy_version="v1",
            family="momentum",
            hypothesis="Shorter ROC window captures faster momentum.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 10},
            neighborhood=[{"window": w} for w in (5, 8, 10, 12, 15, 20)],
            signal_factory=_tpl_factory("momentum"),
        ),
        BaselineCandidate(
            strategy_id="baseline_volatility_breakout",
            strategy_version="v1",
            family="volatility",
            hypothesis="Volatility expansion + momentum confirms breakouts.",
            market="EUR/USD",
            timeframe="15m",
            param_count=1,
            base_params={"window": 20},
            neighborhood=[{"window": w} for w in (15, 18, 20, 22, 25, 30)],
            signal_factory=_vol_factory,
        ),
    ]

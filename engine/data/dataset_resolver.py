"""Resolve Strategy Spec instruments to available datasets (no silent crash)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from engine.nautilus.backtest_adapter import build_golden_ohlcv


@dataclass
class DatasetRef:
    instrument: str
    available: bool
    source: str
    message_zh: str
    broker_specific: bool = False
    timeframe: str = "15m"
    provider: str = "quantlab_golden"
    broker: str | None = None
    venue: str | None = "SIM"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_ALIASES = {
    "EUR/USD": "EUR/USD",
    "EURUSD": "EUR/USD",
    "欧元": "EUR/USD",
    "欧元美元": "EUR/USD",
    "BTCUSDT": "BTCUSDT",
    "BTC/USDT": "BTCUSDT",
    "比特币": "BTCUSDT",
    "XAUUSD": "XAUUSD",
    "黄金": "XAUUSD",
}


def normalize_instrument(raw: str) -> str:
    key = (raw or "").strip()
    return _ALIASES.get(key, _ALIASES.get(key.upper(), key.upper() or key))


def build_btc_golden_ohlcv(n: int = 400, seed: int = 7) -> pd.DataFrame:
    """Deterministic synthetic BTCUSDT 15m bars (second-instrument golden)."""
    import numpy as np

    idx = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    price = 42000 + 15 * t + 200 * np.sin(t / 11) + rng.normal(0, 20, size=n)
    df = pd.DataFrame(index=idx)
    df["open"] = np.array(price, dtype=np.float64, copy=True)
    df["high"] = np.array(price + 40, dtype=np.float64, copy=True)
    df["low"] = np.array(price - 40, dtype=np.float64, copy=True)
    df["close"] = np.array(price, dtype=np.float64, copy=True)
    df["volume"] = np.array(np.full(n, 12.5), dtype=np.float64, copy=True)
    return df


def resolve_dataset(instrument: str, *, timeframe: str = "15m") -> tuple[DatasetRef, pd.DataFrame | None]:
    """Find an in-repo dataset for the instrument; never crash on missing data."""
    inst = normalize_instrument(instrument)
    if inst == "EUR/USD":
        ref = DatasetRef(
            instrument=inst,
            available=True,
            source="golden_synthetic",
            message_zh="已找到 EUR/USD 研究数据集（黄金样本）。",
            broker_specific=True,
            timeframe=timeframe,
            provider="quantlab_golden",
            broker="SIM",
            venue="SIM",
        )
        return ref, build_golden_ohlcv()
    if inst == "BTCUSDT":
        ref = DatasetRef(
            instrument=inst,
            available=True,
            source="golden_synthetic",
            message_zh="已找到 BTCUSDT 研究数据集（黄金样本）。",
            broker_specific=True,
            timeframe=timeframe,
            provider="quantlab_golden",
            broker="BINANCE_SIM",
            venue="BINANCE",
        )
        return ref, build_btc_golden_ohlcv()

    ref = DatasetRef(
        instrument=inst or instrument,
        available=False,
        source="none",
        message_zh=(
            "这个品种目前还没有可用历史数据。你可以：导入数据 / 选择其他数据源 / 更换品种。"
        ),
        broker_specific=True,
        timeframe=timeframe,
    )
    return ref, None

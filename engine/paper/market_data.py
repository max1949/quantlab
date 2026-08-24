"""Market data providers for paper sandbox (public, no auth)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import urllib.error
import urllib.request
import json


@dataclass
class MarketTick:
    instrument: str
    price: float
    event_timestamp: datetime
    receive_timestamp: datetime
    source: str


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_tick(self, instrument: str) -> MarketTick | None:
        raise NotImplementedError


class SyntheticTickProvider(MarketDataProvider):
    """Deterministic provider for tests and offline dev."""

    def __init__(self, *, base_price: float = 50_000.0, step: float = 0.0) -> None:
        self.base_price = base_price
        self.step = step
        self._n = 0

    def fetch_tick(self, instrument: str) -> MarketTick:
        self._n += 1
        now = datetime.now(timezone.utc)
        price = self.base_price + self.step * self._n
        return MarketTick(
            instrument=instrument,
            price=price,
            event_timestamp=now,
            receive_timestamp=now,
            source="synthetic",
        )


class BinancePublicTickerProvider(MarketDataProvider):
    """Binance public REST ticker — no API key required."""

    def __init__(self, *, base_url: str = "https://api.binance.com") -> None:
        self.base_url = base_url.rstrip("/")

    def _symbol(self, instrument: str) -> str:
        # BTCUSDT or BTC/USDT -> BTCUSDT
        return instrument.replace("/", "").replace("-", "").upper()

    def fetch_tick(self, instrument: str) -> MarketTick | None:
        sym = self._symbol(instrument)
        url = f"{self.base_url}/api/v3/ticker/price?symbol={sym}"
        now = datetime.now(timezone.utc)
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
                body = json.loads(resp.read().decode())
            price = float(body["price"])
            return MarketTick(
                instrument=instrument,
                price=price,
                event_timestamp=now,
                receive_timestamp=now,
                source="binance_public",
            )
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
            return None


def resolve_market_data_provider(
    name: str,
    *,
    fallback_synthetic: bool = True,
) -> MarketDataProvider:
    key = (name or "").strip().lower()
    if key in {"binance_public", "binance"}:
        return BinancePublicTickerProvider()
    if key == "synthetic":
        return SyntheticTickProvider()
    if fallback_synthetic:
        return SyntheticTickProvider()
    raise ValueError(f"unknown data provider: {name}")

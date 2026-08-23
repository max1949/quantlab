"""QuantLab trading abstractions — no NautilusTrader imports.

Business / research services should depend on these types only.
Nautilus details stay behind engine.nautilus adapters.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class InstrumentRef:
    symbol: str
    venue: str
    asset_class: str = "FX"


@dataclass(frozen=True)
class BacktestRequest:
    strategy_id: str
    strategy_version: str
    instrument: InstrumentRef
    start: str | None = None
    end: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    starting_balance: str = "1000000 USD"
    engine: str = "NAUTILUS"


@dataclass
class BacktestResult:
    engine: str
    engine_version: str
    strategy_id: str
    strategy_version: str
    status: str
    fill_count: int
    position_count: int
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

"""QuantLab trading adapter transport types — no NautilusTrader imports.

QLN-1: Domain SSOT request/result types live in ``engine.domain.engine_contracts``.
Types here are **legacy adapter transport** for ``engine.nautilus.backtest_adapter`` only.
They are intentionally NOT named BacktestRequest/BacktestResult to avoid canonical collision.
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
class AdapterBacktestRequest:
    """Legacy Nautilus adapter transport (not Domain BacktestRequest)."""

    strategy_id: str
    strategy_version: str
    instrument: InstrumentRef
    start: str | None = None
    end: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    starting_balance: str = "1000000 USD"
    engine: str = "NAUTILUS"


@dataclass
class AdapterBacktestResult:
    """Legacy Nautilus adapter transport result (not Domain BacktestResultContract)."""

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


# Explicit deprecated aliases removed to satisfy DOMAIN_CONCEPT_COLLISION=0.
__all__ = [
    "InstrumentRef",
    "AdapterBacktestRequest",
    "AdapterBacktestResult",
]

"""NautilusTrader adapter layer (ONLY place that imports nautilus_trader)."""

from __future__ import annotations

from engine.nautilus.availability import nautilus_available, nautilus_version
from engine.nautilus.backtest_adapter import NautilusBacktestAdapter

__all__ = [
    "NautilusBacktestAdapter",
    "nautilus_available",
    "nautilus_version",
]

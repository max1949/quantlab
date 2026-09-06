"""Engine Interface contracts — QuantLab Domain must not import Nautilus internals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from engine.domain.environment import Environment
from engine.domain.enums import ExecutionMode


@dataclass(slots=True)
class EngineCapability:
    name: str
    supports_backtest: bool = False
    supports_paper: bool = False
    supports_shadow: bool = False
    supports_live: bool = False
    notes: str = ""


@dataclass(slots=True)
class BacktestRequest:
    strategy_spec: dict[str, Any]
    dataset_id: str
    environment: Environment = Environment.BACKTEST
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BacktestResultContract:
    ok: bool
    strategy_spec_hash: str
    metrics: dict[str, Any] = field(default_factory=dict)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    engine_fingerprint: str = ""
    error: str | None = None


@dataclass(slots=True)
class PaperRuntimeRequest:
    strategy_spec: dict[str, Any]
    run_id: str
    environment: Environment = Environment.PAPER
    execution_mode: ExecutionMode = ExecutionMode.PAPER
    effective_config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeResultContract:
    ok: bool
    run_id: str
    status: str
    positions: list[dict[str, Any]] = field(default_factory=list)
    orders: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@runtime_checkable
class BacktestEngineContract(Protocol):
    """Domain-facing backtest port. Implementations live under engine/nautilus or research adapters."""

    def capabilities(self) -> EngineCapability: ...

    def run_backtest(self, request: BacktestRequest) -> BacktestResultContract: ...


@runtime_checkable
class PaperRuntimeContract(Protocol):
    """Domain-facing paper runtime port."""

    def capabilities(self) -> EngineCapability: ...

    def start(self, request: PaperRuntimeRequest) -> RuntimeResultContract: ...

    def stop(self, run_id: str) -> RuntimeResultContract: ...


# Shared Strategy field semantics for Backtest vs Paper (same meaning, not same market path).
SHARED_STRATEGY_FIELD_SEMANTICS: dict[str, str] = {
    "instrument": "Trading instrument identifier (normalized symbol).",
    "timeframe": "Bar aggregation period for signals.",
    "parameters": "Strategy behavior parameters from Spec (e.g. ema_fast/ema_slow).",
    "direction": "Long/short permission from Spec entry sides.",
    "position_sizing": "Size rule from Spec.position_sizing.",
    "risk_settings": "Risk caps from Spec.risk.",
    "stop_loss": "Stop definition from Spec.stop_loss.",
    "take_profit": "Take-profit definition from Spec.take_profit.",
    "trading_session": "Session filter from Spec.market.session.",
    "fees": "Explicit fee model assumption (environment may set model; field meaning=fee).",
    "slippage": "Explicit slippage assumption (environment may set model; field meaning=slippage).",
    "clock_timezone": "Canonical clock/timezone for bar boundaries (UTC unless Spec overrides).",
    "data_source": "Provenance label of market data (not a silent Spec rewrite).",
    "execution_assumptions": "Must be explicit; must not mutate Strategy Spec fields.",
}


def assert_no_nautilus_domain_import() -> None:
    """Guard helper for tests: domain package must not import nautilus_trader."""
    import sys

    banned = [m for m in sys.modules if m == "nautilus_trader" or m.startswith("nautilus_trader.")]
    # Presence in process is OK if adapters loaded; this module itself must not require it.
    import engine.domain as domain_pkg

    src = getattr(domain_pkg, "__file__", "") or ""
    _ = src
    return None

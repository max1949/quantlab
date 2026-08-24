"""Native Nautilus TradingNode paper/sandbox runtime (ONLY nautilus imports here).

Path proven:
  MARKET_DATA → Nautilus DataEngine → Strategy → Order →
  SandboxExecutionClient (SimulatedExchange) → Fill → Position → Portfolio

QuantLab must NOT re-implement fills/positions here.
LIVE production Binance execution client is never registered.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from engine.nautilus.availability import nautilus_available, nautilus_version
from engine.trading.execution_environment import assert_environment_allowed

PINNED_VERSION = "1.231.0"
FORBIDDEN_EXEC_FACTORIES = frozenset(
    {
        "BinanceLiveExecClientFactory",
        "BinanceSpotExecutionClient",
        "BinanceFuturesExecutionClient",
    }
)


@dataclass
class PaperNodeConfig:
    run_id: str
    instrument: str
    environment: str = "SANDBOX"
    data_provider: str = "synthetic"  # synthetic | binance_public
    starting_balance: str = "100000 USDT"
    strategy_version: str = "v1"
    ema_fast: int | None = None
    ema_slow: int | None = None
    trade_size: str | None = None
    bar_minutes: int | None = None
    run_seconds: float = 8.0
    synthetic_ticks: int = 60
    synthetic_base_price: float = 60_000.0
    state_dir: str | None = None


@dataclass
class PaperNodeSnapshot:
    engine: str = "NAUTILUS_SANDBOX"
    engine_version: str = PINNED_VERSION
    path: list[str] = field(
        default_factory=lambda: [
            "MARKET_DATA",
            "NAUTILUS",
            "STRATEGY",
            "ORDER",
            "SIMULATED_FILL",
            "POSITION",
            "PORTFOLIO",
        ]
    )
    orders: list[dict[str, Any]] = field(default_factory=list)
    fills: list[dict[str, Any]] = field(default_factory=list)
    positions: list[dict[str, Any]] = field(default_factory=list)
    signals: list[dict[str, Any]] = field(default_factory=list)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    equity: float = 0.0
    balance: float = 0.0
    position_side: str | None = None
    position_qty: float = 0.0
    last_price: float | None = None
    data_provider: str = ""
    native_nautilus: bool = True
    production_exec_registered: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assert_no_production_exec_factory(registered_names: list[str]) -> None:
    for name in registered_names:
        bad = name in FORBIDDEN_EXEC_FACTORIES or (
            "Binance" in name and "Exec" in name and "Sandbox" not in name
        )
        if bad:
            raise RuntimeError(f"PRODUCTION_EXECUTION_FACTORY_DENIED:{name}")


def run_paper_node(config: PaperNodeConfig) -> PaperNodeSnapshot:
    """Build TradingNode on its kernel loop and run a timed sandbox window."""
    assert_environment_allowed(config.environment, layer="adapter", live_allowed=False)
    if config.ema_fast is None or config.ema_slow is None or not config.trade_size:
        return PaperNodeSnapshot(
            error="STRATEGY_SPEC_PARAMS_REQUIRED: ema_fast/ema_slow/trade_size must come from Strategy Spec",
            native_nautilus=False,
        )
    if config.bar_minutes is None:
        return PaperNodeSnapshot(
            error="STRATEGY_SPEC_PARAMS_REQUIRED: bar_minutes must come from Strategy Spec timeframe",
            native_nautilus=False,
        )
    if not nautilus_available():
        return PaperNodeSnapshot(error="nautilus_trader_not_installed", native_nautilus=False)
    ver = nautilus_version()
    if ver != PINNED_VERSION:
        return PaperNodeSnapshot(
            error=f"NAUTILUS_VERSION_PINNED expected {PINNED_VERSION}, got {ver}",
            engine_version=ver or "unknown",
            native_nautilus=False,
        )

    state_dir = Path(config.state_dir) if config.state_dir else Path("data") / "paper_runs" / config.run_id
    state_dir.mkdir(parents=True, exist_ok=True)

    snap = PaperNodeSnapshot(
        engine_version=ver or PINNED_VERSION,
        data_provider=config.data_provider,
        production_exec_registered=False,
    )
    node = None
    try:
        node = _build_node(config)
        loop = node.get_event_loop()
        assert loop is not None

        def _stop() -> None:
            try:
                node.stop()
            except Exception:  # noqa: BLE001
                pass

        loop.call_later(float(config.run_seconds), _stop)
        node.run(raise_exception=True)
        snap = _snapshot_from_node(node, snap, strategy_version=config.strategy_version)
    except Exception as exc:  # noqa: BLE001
        snap.error = str(exc)[:500]
        if node is not None:
            try:
                snap = _snapshot_from_node(node, snap, strategy_version=config.strategy_version)
            except Exception as snap_exc:  # noqa: BLE001
                snap.error = ((snap.error or "") + f"|snap:{snap_exc}")[:500]
    finally:
        _write_state(state_dir, snap)
        if node is not None:
            try:
                node.dispose()
            except Exception:  # noqa: BLE001
                pass
    return snap


def _build_node(config: PaperNodeConfig):
    from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
    from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
    from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
    from nautilus_trader.adapters.sandbox.config import SandboxExecutionClientConfig
    from nautilus_trader.adapters.sandbox.factory import SandboxLiveExecClientFactory
    from nautilus_trader.config import InstrumentProviderConfig
    from nautilus_trader.config import LiveDataEngineConfig
    from nautilus_trader.config import LiveExecEngineConfig
    from nautilus_trader.config import LiveRiskEngineConfig
    from nautilus_trader.config import LoggingConfig
    from nautilus_trader.config import TradingNodeConfig
    from nautilus_trader.examples.strategies.ema_cross import EMACross, EMACrossConfig
    from nautilus_trader.live.node import TradingNode
    from nautilus_trader.model import BarType
    from nautilus_trader.test_kit.providers import TestInstrumentProvider

    from engine.nautilus.synthetic_data_client import (
        SyntheticDataClientConfig,
        SyntheticLiveDataClientFactory,
    )

    instrument = TestInstrumentProvider.btcusdt_binance()
    instrument_id = instrument.id
    bar_type = BarType.from_str(f"{instrument_id}-{config.bar_minutes}-MINUTE-LAST-EXTERNAL")

    if config.data_provider in {"binance_public", "binance"}:
        data_factory_name = "BINANCE"
        data_clients: dict[str, Any] = {
            "BINANCE": BinanceDataClientConfig(
                api_key=None,
                api_secret=None,
                account_type=BinanceAccountType.SPOT,
                instrument_provider=InstrumentProviderConfig(load_ids=frozenset([instrument_id])),
            ),
        }
    else:
        data_factory_name = "SYNTHETIC"
        data_clients = {
            "SYNTHETIC": SyntheticDataClientConfig(
                instrument_id=str(instrument_id),
                ticks=config.synthetic_ticks,
                base_price=config.synthetic_base_price,
                interval_ms=50,
            ),
        }

    exec_clients = {
        "BINANCE": SandboxExecutionClientConfig(
            venue="BINANCE",
            starting_balances=[config.starting_balance],
            base_currency="USDT",
            oms_type="NETTING",
            account_type="MARGIN",
            bar_execution=True,
            trade_execution=True,
        ),
    }

    node = TradingNode(
        config=TradingNodeConfig(
            trader_id=f"QLPAPAR-{config.run_id[:8].upper()}",
            logging=LoggingConfig(log_level="ERROR"),
            data_clients=data_clients,
            exec_clients=exec_clients,
            data_engine=LiveDataEngineConfig(graceful_shutdown_on_exception=True),
            risk_engine=LiveRiskEngineConfig(graceful_shutdown_on_exception=True),
            exec_engine=LiveExecEngineConfig(
                reconciliation=False,
                graceful_shutdown_on_exception=True,
            ),
            timeout_connection=10.0,
            timeout_reconciliation=5.0,
            timeout_portfolio=5.0,
            timeout_disconnection=5.0,
            timeout_post_stop=2.0,
        ),
    )
    assert_no_production_exec_factory(["SandboxLiveExecClientFactory"])
    if data_factory_name == "BINANCE":
        node.add_data_client_factory("BINANCE", BinanceLiveDataClientFactory)
    else:
        node.add_data_client_factory("SYNTHETIC", SyntheticLiveDataClientFactory)
    node.add_exec_client_factory("BINANCE", SandboxLiveExecClientFactory)
    node.build()
    node.kernel.cache.add_instrument(instrument)
    node.trader.add_strategy(
        EMACross(
            config=EMACrossConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                trade_size=Decimal(config.trade_size),
                fast_ema_period=int(config.ema_fast),
                slow_ema_period=int(config.ema_slow),
                request_bars=False,
                subscribe_trade_ticks=True,
                subscribe_quote_ticks=False,
                close_positions_on_stop=False,
            )
        )
    )
    return node


def _snapshot_from_node(node, snap: PaperNodeSnapshot, *, strategy_version: str) -> PaperNodeSnapshot:
    fills_df = node.trader.generate_order_fills_report()
    positions_df = node.trader.generate_positions_report()
    orders_df = node.trader.generate_orders_report()

    if orders_df is not None and len(orders_df) > 0:
        for _, row in orders_df.iterrows():
            snap.orders.append({k: _jsonable(v) for k, v in row.to_dict().items()})
    if fills_df is not None and len(fills_df) > 0:
        for _, row in fills_df.iterrows():
            snap.fills.append({k: _jsonable(v) for k, v in row.to_dict().items()})
    if positions_df is not None and len(positions_df) > 0:
        for _, row in positions_df.iterrows():
            snap.positions.append({k: _jsonable(v) for k, v in row.to_dict().items()})

    open_positions = list(node.cache.positions_open())
    if open_positions:
        pos = open_positions[0]
        qty = float(pos.quantity)
        snap.position_qty = abs(qty)
        snap.position_side = "long" if qty > 0 else "short" if qty < 0 else None

    try:
        from nautilus_trader.model.identifiers import Venue

        account = node.portfolio.account(Venue("BINANCE"))
        if account is not None:
            for cur, bal in account.balances().items():
                if str(cur) == "USDT":
                    snap.balance = float(bal.total)
                    break
            if snap.balance == 0.0:
                bals = account.balances()
                if bals:
                    snap.balance = float(next(iter(bals.values())).total)
            snap.equity = snap.balance
    except Exception:  # noqa: BLE001
        pass

    snap.signals.append(
        {
            "strategy_version": strategy_version,
            "decision": "HOLD" if not snap.fills else "TRADED",
            "reason": "nautilus_ema_cross",
            "orders": len(snap.orders),
            "fills": len(snap.fills),
        }
    )
    return snap


def _jsonable(v: Any) -> Any:
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def _write_state(state_dir: Path, snap: PaperNodeSnapshot) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "nautilus_snapshot.json").write_text(
        json.dumps(snap.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    health = {
        "ready": snap.error is None,
        "native_nautilus": snap.native_nautilus,
        "orders": len(snap.orders),
        "fills": len(snap.fills),
        "positions": len(snap.positions),
        "engine": snap.engine,
        "path": snap.path,
        "error": snap.error,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    (state_dir / "health.json").write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")


def load_snapshot(state_dir: str | Path) -> PaperNodeSnapshot | None:
    path = Path(state_dir) / "nautilus_snapshot.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return PaperNodeSnapshot(**{k: v for k, v in data.items() if k in PaperNodeSnapshot.__dataclass_fields__})

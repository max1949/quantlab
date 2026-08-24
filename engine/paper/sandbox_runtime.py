"""Sandbox paper runtime — tick loop for paper-runner process."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from engine.paper.gates import run_realtime_data_gate
from engine.paper.kill_switch import KillSwitchState, check_kill_switch
from engine.paper.market_data import MarketDataProvider, MarketTick
from engine.paper.order_lifecycle import PaperOrderState, create_market_order
from engine.paper.realtime_data_policy import RealtimeDataPolicy
from engine.paper.recovery import RecoverySnapshot, should_allow_new_entry
from engine.paper.risk_policy import PaperRiskPolicy, evaluate_risk
from engine.paper.signal_engine import EmaSignalEngine, SignalDecision
from engine.trading.execution_environment import assert_environment_allowed


class PaperRunStore(Protocol):
    def get_kill_state(self) -> KillSwitchState: ...
    def get_recovery_snapshot(self) -> RecoverySnapshot: ...
    def get_metrics(self) -> dict[str, Any]: ...
    def persist_tick(
        self,
        *,
        tick: MarketTick,
        data_gate: dict[str, Any],
        signal: SignalDecision | None,
        order: PaperOrderState | None,
        position_side: str | None,
        position_qty: float,
        balance: float,
        pnl: float,
        events: list[dict[str, Any]],
    ) -> None: ...
    def mark_status(self, status: str, *, detail: str = "") -> None: ...


@dataclass
class SandboxRuntimeConfig:
    run_id: str
    instrument: str = "BTCUSDT"
    environment: str = "SANDBOX"
    starting_balance: float = 100_000.0
    currency: str = "USDT"
    trade_notional: float = 10_000.0
    strategy_version: str = "v1"
    ema_fast: int = 10
    ema_slow: int = 20
    simulated_balance: bool = True


@dataclass
class SandboxRuntimeState:
    balance: float
    position_side: str | None = None
    position_qty: float = 0.0
    entry_price: float | None = None
    realized_pnl: float = 0.0
    orders_total: int = 0
    fills_total: int = 0
    signals_total: int = 0
    data_stale: bool = False
    risk_paused: bool = False
    last_tick: MarketTick | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


class SandboxPaperRuntime:
    """One PaperRun = one runtime instance (intended for isolated process)."""

    def __init__(
        self,
        *,
        config: SandboxRuntimeConfig,
        store: PaperRunStore,
        market_data: MarketDataProvider,
        risk_policy: PaperRiskPolicy | None = None,
        data_policy: RealtimeDataPolicy | None = None,
    ) -> None:
        assert_environment_allowed(config.environment, layer="adapter")
        self.config = config
        self.store = store
        self.market_data = market_data
        self.risk_policy = risk_policy or PaperRiskPolicy()
        self.data_policy = data_policy or RealtimeDataPolicy()
        self.engine = EmaSignalEngine(
            fast=config.ema_fast,
            slow=config.ema_slow,
            strategy_version=config.strategy_version,
        )
        snap = store.get_recovery_snapshot()
        self.state = SandboxRuntimeState(balance=config.starting_balance)
        if snap.has_open_position:
            self.state.position_side = snap.open_side
            self.state.position_qty = snap.open_quantity
            self.engine.set_position(snap.open_side)

    def tick_once(self) -> dict[str, Any]:
        if check_kill_switch(self.store.get_kill_state()) == "DENY":
            self.store.mark_status("KILLED", detail="kill_switch")
            return {"status": "KILLED", "reason": "kill_switch"}

        tick = self.market_data.fetch_tick(self.config.instrument)
        if tick is None:
            self.state.data_stale = True
            gate = run_realtime_data_gate(
                last_event_ts=None,
                instrument_loaded=True,
                stream_active=False,
                policy=self.data_policy,
            )
            self.store.persist_tick(
                tick=MarketTick(
                    self.config.instrument,
                    0.0,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    "none",
                ),
                data_gate=gate.to_dict(),
                signal=None,
                order=None,
                position_side=self.state.position_side,
                position_qty=self.state.position_qty,
                balance=self.state.balance,
                pnl=self.state.realized_pnl,
                events=[{"code": "DATA_STALE", "message_zh": "行情不可用"}],
            )
            return {"status": "DATA_STALE", "gate": gate.to_dict()}

        self.state.last_tick = tick
        gate = run_realtime_data_gate(
            last_event_ts=tick.event_timestamp,
            receive_ts=tick.receive_timestamp,
            instrument_loaded=True,
            stream_active=True,
            policy=self.data_policy,
        )
        self.state.data_stale = gate.status == "FAIL" or not gate.data_fresh

        signal = self.engine.update(
            tick.price,
            timestamp=tick.event_timestamp.isoformat(),
            instrument=self.config.instrument,
        )
        self.state.signals_total += 1

        order: PaperOrderState | None = None
        events: list[dict[str, Any]] = []

        if self.state.risk_paused:
            events.append({"code": "RISK_PAUSED", "message_zh": "策略已风控暂停"})
        elif self.state.data_stale and signal.decision in {"BUY", "SELL"}:
            events.append({"code": "DATA_STALE", "message_zh": "行情过期，禁止新开仓"})
        else:
            order, evs = self._maybe_trade(signal, tick.price)
            events.extend(evs)

        self.store.persist_tick(
            tick=tick,
            data_gate=gate.to_dict(),
            signal=signal,
            order=order,
            position_side=self.state.position_side,
            position_qty=self.state.position_qty,
            balance=self.state.balance,
            pnl=self.state.realized_pnl,
            events=events,
        )
        return {
            "status": "RUNNING",
            "price": tick.price,
            "signal": signal.to_dict(),
            "data_gate": gate.to_dict(),
            "position_side": self.state.position_side,
            "events": events,
        }

    def _maybe_trade(
        self, signal: SignalDecision, price: float
    ) -> tuple[PaperOrderState | None, list[dict[str, Any]]]:
        events: list[dict[str, Any]] = []
        decision = signal.decision
        if decision not in {"BUY", "SELL", "EXIT"}:
            return None, events

        snap = self.store.get_recovery_snapshot()
        side = "long" if decision in {"BUY"} else "short" if decision == "SELL" else None
        if decision == "EXIT" and self.state.position_side:
            side = "flat"

        new_entry = decision in {"BUY", "SELL"} and self.state.position_side is None
        if new_entry:
            ok, msg = should_allow_new_entry(
                signal_side="long" if decision == "BUY" else "short",
                snapshot=snap,
            )
            if not ok:
                events.append({"code": "DUPLICATE_ENTRY_BLOCKED", "message_zh": msg})
                return None, events

        qty = self.config.trade_notional / max(price, 1e-9)
        order_side = "buy" if decision == "BUY" else "sell"
        if decision == "EXIT":
            order_side = "sell" if self.state.position_side == "long" else "buy"
            qty = self.state.position_qty

        risk = evaluate_risk(
            self.risk_policy,
            order_notional=qty * price,
            position_notional=(self.state.position_qty or 0) * price,
            open_positions=1 if self.state.position_side else 0,
            strategy_exposure=(self.state.position_qty or 0) * price,
            daily_pnl=self.state.realized_pnl,
            drawdown=0.0,
            consecutive_losses=0,
            orders_last_minute=0,
            new_entry=new_entry,
        )
        if not risk.allowed:
            for ev in risk.events:
                events.append(ev.to_dict())
            if risk.action == "PAUSE_STRATEGY":
                self.state.risk_paused = True
            return None, events

        order = create_market_order(
            instrument=self.config.instrument,
            side=order_side,
            quantity=qty,
        )
        order.submit()
        order.accept()
        fee = qty * price * 0.0004
        order.fill(price=price, quantity=qty, fee=fee)
        self.state.orders_total += 1
        self.state.fills_total += 1

        if decision == "EXIT" or (self.state.position_side and decision in {"BUY", "SELL"}):
            if self.state.position_side == "long" and self.state.entry_price:
                self.state.realized_pnl += (price - self.state.entry_price) * self.state.position_qty - fee
            elif self.state.position_side == "short" and self.state.entry_price:
                self.state.realized_pnl += (self.state.entry_price - price) * self.state.position_qty - fee
            self.state.position_side = None
            self.state.position_qty = 0.0
            self.state.entry_price = None
            self.engine.set_position(None)
        elif decision == "BUY":
            self.state.position_side = "long"
            self.state.position_qty = qty
            self.state.entry_price = price
            self.engine.set_position("long")
        elif decision == "SELL":
            self.state.position_side = "short"
            self.state.position_qty = qty
            self.state.entry_price = price
            self.engine.set_position("short")

        self.state.balance = self.config.starting_balance + self.state.realized_pnl
        return order, events

    def health(self) -> dict[str, Any]:
        return {
            "run_id": self.config.run_id,
            "environment": self.config.environment,
            "simulated_balance": self.config.simulated_balance,
            "data_stale": self.state.data_stale,
            "risk_paused": self.state.risk_paused,
            "orders_total": self.state.orders_total,
            "fills_total": self.state.fills_total,
            "signals_total": self.state.signals_total,
        }

    def ready(self) -> dict[str, Any]:
        ok = (
            self.config.instrument
            and self.risk_policy is not None
            and self.engine is not None
        )
        degraded = self.state.data_stale
        return {
            "ready": ok and not degraded,
            "degraded": degraded,
            "checks": {
                "runtime_started": True,
                "instrument_loaded": bool(self.config.instrument),
                "risk_loaded": self.risk_policy is not None,
                "strategy_loaded": self.engine is not None,
                "market_data_connected": self.state.last_tick is not None,
            },
        }

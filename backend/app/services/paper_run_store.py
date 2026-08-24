"""DB-backed store for SandboxPaperRuntime."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.paper_run import (
    PaperRun,
    PaperRunEvent,
    PaperRunFill,
    PaperRunOrder,
    PaperRunPosition,
    SignalDecisionRecord,
)
from engine.paper.kill_switch import KillSwitchState
from engine.paper.market_data import MarketTick
from engine.paper.order_lifecycle import PaperOrderState
from engine.paper.recovery import RecoverySnapshot
from engine.paper.signal_engine import SignalDecision


class DbPaperRunStore:
    def __init__(self, db: Session, run: PaperRun) -> None:
        self.db = db
        self.run = run

    def get_kill_state(self) -> KillSwitchState:
        s = get_settings()
        return KillSwitchState(
            global_active=s.execution_kill_switch or self.run.global_kill_switch,
            paper_run_active=self.run.kill_switch_active,
            strategy_active=self.run.strategy_kill_switch,
            reason=self.run.stop_reason,
        )

    def get_recovery_snapshot(self) -> RecoverySnapshot:
        return RecoverySnapshot(
            has_open_position=bool(self.run.position_side and float(self.run.position_qty or 0) > 0),
            open_side=self.run.position_side,
            open_quantity=float(self.run.position_qty or 0),
            recovered_from_crash=self.run.restart_count > 0,
            restart_count=self.run.restart_count,
        )

    def get_metrics(self) -> dict:
        return dict(self.run.metrics or {})

    def mark_status(self, status: str, *, detail: str = "") -> None:
        self.run.status = status
        if detail:
            self.run.stop_reason = detail[:200]
        if status in {"STOPPED", "FAILED", "KILLED"}:
            self.run.ended_at = datetime.now(timezone.utc)
        self.db.commit()

    def persist_tick(
        self,
        *,
        tick: MarketTick,
        data_gate: dict,
        signal: SignalDecision | None,
        order: PaperOrderState | None,
        position_side: str | None,
        position_qty: float,
        balance: float,
        pnl: float,
        events: list[dict],
    ) -> None:
        self.run.status = "RUNNING"
        self.run.last_market_event_at = tick.event_timestamp
        self.run.market_data_age_seconds = data_gate.get("event_age_seconds")
        self.run.data_gate_status = str(data_gate.get("status", ""))
        self.run.data_stale = not bool(data_gate.get("data_fresh"))
        self.run.position_side = position_side
        self.run.position_qty = position_qty
        self.run.current_balance = balance
        self.run.realized_pnl = pnl
        if self.run.started_at is None:
            self.run.started_at = datetime.now(timezone.utc)

        metrics = dict(self.run.metrics or {})
        metrics["signals_total"] = int(metrics.get("signals_total", 0)) + (1 if signal else 0)
        metrics["orders_total"] = int(metrics.get("orders_total", 0)) + (1 if order else 0)
        metrics["market_data_events_total"] = int(metrics.get("market_data_events_total", 0)) + 1
        if tick.price:
            metrics["last_price"] = tick.price
        self.run.metrics = metrics

        if signal:
            self.db.add(
                SignalDecisionRecord(
                    paper_run_id=self.run.id,
                    strategy_version=signal.strategy_version,
                    instrument=signal.instrument,
                    decision=signal.decision,
                    reason=signal.reason,
                    conditions=signal.conditions,
                    condition_values=signal.condition_values,
                    decided_at=datetime.fromisoformat(signal.timestamp.replace("Z", "+00:00"))
                    if signal.timestamp
                    else datetime.now(timezone.utc),
                )
            )

        if order:
            row = PaperRunOrder(
                id=uuid.UUID(order.order_id),
                paper_run_id=self.run.id,
                client_order_id=order.order_id,
                instrument=order.instrument,
                side=order.side,
                quantity=order.quantity,
                price=order.price,
                status=order.state.value,
                lifecycle_events=[e.__dict__ if hasattr(e, "__dict__") else e for e in order.events],
                signal_reason=signal.reason if signal else "",
            )
            self.db.add(row)
            if order.price is not None and order.filled_quantity:
                self.db.add(
                    PaperRunFill(
                        paper_run_id=self.run.id,
                        order_id=row.id,
                        instrument=order.instrument,
                        side=order.side,
                        quantity=order.filled_quantity,
                        price=order.price,
                        fee=order.fee,
                        simulated=True,
                    )
                )

        if position_side and position_qty > 0:
            pos = self.db.scalars(
                select(PaperRunPosition).where(
                    PaperRunPosition.paper_run_id == self.run.id,
                    PaperRunPosition.is_open.is_(True),
                )
            ).first()
            if pos is None:
                pos = PaperRunPosition(
                    paper_run_id=self.run.id,
                    instrument=self.run.instrument,
                    side=position_side,
                    quantity=position_qty,
                    avg_price=float(tick.price or 0),
                    is_open=True,
                    opened_at=datetime.now(timezone.utc),
                )
                self.db.add(pos)
            else:
                pos.side = position_side
                pos.quantity = position_qty
                pos.avg_price = float(tick.price or pos.avg_price)
        else:
            for pos in self.db.scalars(
                select(PaperRunPosition).where(
                    PaperRunPosition.paper_run_id == self.run.id,
                    PaperRunPosition.is_open.is_(True),
                )
            ).all():
                pos.is_open = False
                pos.closed_at = datetime.now(timezone.utc)

        for ev in events:
            code = str(ev.get("code", "EVENT"))
            self.db.add(
                PaperRunEvent(
                    paper_run_id=self.run.id,
                    code=code,
                    message_zh=str(ev.get("message_zh", code)),
                    payload=ev,
                )
            )
            alerts = list(self.run.alerts or [])
            alerts.append({"code": code, "message_zh": ev.get("message_zh", code)})
            self.run.alerts = alerts[-20:]

        self.db.commit()

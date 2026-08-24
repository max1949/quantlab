#!/usr/bin/env python3
"""Standalone paper-runner: one PaperRun = one isolated Nautilus TradingNode process.

QuantLab orchestrates + persists. Nautilus owns market data → strategy → sandbox fills.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.models.paper_run import (
    PaperRun,
    PaperRunEvent,
    PaperRunFill,
    PaperRunOrder,
    PaperRunPosition,
    PaperRunStatus,
    SignalDecisionRecord,
)
from engine.paper.portfolio import portfolio_from_snapshot
from engine.strategies.runtime_params import runtime_params_from_effective_config
from engine.trading.execution_environment import assert_environment_allowed


def _state_dir(run_id: str) -> Path:
    d = ROOT / "data" / "paper_runs" / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _persist_snapshot(db, run: PaperRun, snap: dict) -> None:
    run.engine = "NAUTILUS_SANDBOX"
    run.engine_version = str(snap.get("engine_version") or "1.231.0")
    run.realized_pnl = float(snap.get("realized_pnl") or 0)
    run.position_side = snap.get("position_side")
    run.position_qty = float(snap.get("position_qty") or 0)
    if snap.get("balance"):
        run.current_balance = float(snap["balance"])
    metrics = dict(run.metrics or {})
    metrics = portfolio_from_snapshot(
        starting_balance=float(run.starting_balance),
        snap=snap,
        existing_metrics=metrics,
        started_at=run.started_at,
        ended_at=datetime.now(timezone.utc),
    )
    run.unrealized_pnl = float(metrics.get("unrealized_pnl") or 0)
    metrics.update(
        {
            "orders_total": len(snap.get("orders") or []),
            "fills_total": len(snap.get("fills") or []),
            "positions_total": len(snap.get("positions") or []),
            "native_nautilus": bool(snap.get("native_nautilus", True)),
            "path": snap.get("path") or [],
            "last_price": snap.get("last_price"),
        }
    )
    run.metrics = metrics
    if run.started_at is None:
        run.started_at = datetime.now(timezone.utc)

    for sig in snap.get("signals") or []:
        db.add(
            SignalDecisionRecord(
                paper_run_id=run.id,
                strategy_version=str(sig.get("strategy_version") or run.strategy_spec_version),
                instrument=run.instrument,
                decision=str(sig.get("decision") or "HOLD"),
                reason=str(sig.get("reason") or ""),
                conditions=[],
                condition_values={k: v for k, v in sig.items() if isinstance(v, (int, float, str))},
            )
        )

    for o in snap.get("orders") or []:
        client_id = str(o.get("client_order_id") or o.get("ClientOrderId") or uuid.uuid4())
        existing = db.scalars(
            select(PaperRunOrder).where(
                PaperRunOrder.paper_run_id == run.id,
                PaperRunOrder.client_order_id == client_id,
            )
        ).first()
        if existing:
            continue
        order = PaperRunOrder(
            paper_run_id=run.id,
            client_order_id=client_id,
            instrument=run.instrument,
            side=str(o.get("side") or o.get("Side") or "buy").lower(),
            quantity=float(o.get("quantity") or o.get("Quantity") or 0),
            price=float(o["avg_px"]) if o.get("avg_px") not in (None, "") else None,
            status=str(o.get("status") or o.get("Status") or "OrderFilled"),
            lifecycle_events=[{"event_type": "nautilus_order", "raw": o}],
            signal_reason="nautilus_ema_cross",
        )
        db.add(order)
        db.flush()

    for f in snap.get("fills") or []:
        last_order = db.scalars(
            select(PaperRunOrder)
            .where(PaperRunOrder.paper_run_id == run.id)
            .order_by(PaperRunOrder.created_at.desc())
        ).first()
        if last_order is None:
            last_order = PaperRunOrder(
                paper_run_id=run.id,
                client_order_id=str(uuid.uuid4()),
                instrument=run.instrument,
                side=str(f.get("side") or "buy").lower(),
                quantity=float(f.get("last_qty") or f.get("quantity") or 0),
                price=float(f.get("last_px") or f.get("price") or 0),
                status="OrderFilled",
                lifecycle_events=[],
                signal_reason="nautilus_fill",
            )
            db.add(last_order)
            db.flush()
        db.add(
            PaperRunFill(
                paper_run_id=run.id,
                order_id=last_order.id,
                instrument=run.instrument,
                side=last_order.side,
                quantity=float(f.get("last_qty") or f.get("quantity") or last_order.quantity),
                price=float(f.get("last_px") or f.get("price") or last_order.price or 0),
                fee=0.0,
                simulated=True,
            )
        )

    if run.position_side and float(run.position_qty or 0) > 0:
        open_pos = db.scalars(
            select(PaperRunPosition).where(
                PaperRunPosition.paper_run_id == run.id,
                PaperRunPosition.is_open.is_(True),
            )
        ).first()
        if open_pos is None:
            db.add(
                PaperRunPosition(
                    paper_run_id=run.id,
                    instrument=run.instrument,
                    side=run.position_side,
                    quantity=run.position_qty,
                    avg_price=float(snap.get("last_price") or 0),
                    is_open=True,
                    opened_at=datetime.now(timezone.utc),
                )
            )
        else:
            open_pos.side = run.position_side
            open_pos.quantity = run.position_qty

    db.add(
        PaperRunEvent(
            paper_run_id=run.id,
            code="NAUTILUS_SNAPSHOT",
            message_zh="Nautilus TradingNode 快照已落库",
            payload={"orders": len(snap.get("orders") or []), "fills": len(snap.get("fills") or [])},
        )
    )
    if snap.get("error"):
        run.status = PaperRunStatus.FAILED.value
        run.failure_reason = str(snap["error"])[:500]
    db.commit()


def run_nautilus(run_id: uuid.UUID, *, seconds: float = 8.0, db=None) -> dict:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        run = db.get(PaperRun, run_id)
        if run is None:
            return {"error": "run_not_found"}

        assert_environment_allowed(run.environment, layer="adapter", live_allowed=False)

        if run.kill_switch_active or run.global_kill_switch or run.strategy_kill_switch:
            run.status = PaperRunStatus.KILLED.value
            run.stop_reason = "kill_switch_active"
            run.ended_at = datetime.now(timezone.utc)
            db.commit()
            return {"ok": False, "error": "kill_switch_active", "native_nautilus": True}

        # Recovery: prior crash with open position OR prior Nautilus snapshot on disk
        state = _state_dir(str(run.id))
        prev = state / "nautilus_snapshot.json"
        recovered = False
        prior_failed = (run.status or "").upper() in {"FAILED", "KILLED"} and bool(run.position_side) and float(
            run.position_qty or 0
        ) > 0
        if prior_failed or (prev.exists() and run.position_side and float(run.position_qty or 0) > 0):
            recovered = True
            run.restart_count = int(run.restart_count or 0) + 1
            db.add(
                PaperRunEvent(
                    paper_run_id=run.id,
                    code="STATE_RECOVERY",
                    message_zh="从落盘/崩溃状态恢复，禁止重复开仓逻辑由 RecoverySnapshot 控制",
                    payload={
                        "position_side": run.position_side,
                        "position_qty": float(run.position_qty),
                        "prior_status": run.status,
                        "snapshot_exists": prev.exists(),
                    },
                )
            )

        run.status = PaperRunStatus.RUNNING.value
        run.runner_pid = os.getpid()
        db.commit()

        from engine.nautilus.paper_node import PaperNodeConfig, run_paper_node

        runtime = runtime_params_from_effective_config(run.effective_config or {})
        eff = run.effective_config or {}
        snap_obj = run_paper_node(
            PaperNodeConfig(
                run_id=str(run.id),
                instrument=runtime["instrument"],
                environment=run.environment,
                data_provider=run.data_provider or "synthetic",
                starting_balance=f"{float(run.starting_balance):.0f} {run.currency}",
                strategy_version=run.strategy_spec_version,
                trade_size=str(runtime["trade_size"]),
                bar_minutes=int(runtime["bar_minutes"]),
                ema_fast=int(runtime["ema_fast"]),
                ema_slow=int(runtime["ema_slow"]),
                run_seconds=seconds,
                synthetic_ticks=int(eff.get("synthetic_ticks", 60)),
                state_dir=str(state),
            )
        )
        snap = snap_obj.to_dict()

        # Duplicate entry guard after recovery: keep prior position, do not invent second entry
        if recovered and run.position_side:
            snap["position_side"] = run.position_side
            snap["position_qty"] = float(run.position_qty)
            snap.setdefault("signals", []).append(
                {
                    "strategy_version": run.strategy_spec_version,
                    "decision": "HOLD",
                    "reason": "restart_duplicate_entry_blocked",
                }
            )

        _persist_snapshot(db, run, snap)

        if run.kill_switch_active:
            run.status = PaperRunStatus.KILLED.value
            run.stop_reason = "kill_switch"
        elif snap.get("error"):
            run.status = PaperRunStatus.FAILED.value
        else:
            run.status = PaperRunStatus.STOPPED.value
            run.stop_reason = "nautilus_window_complete"
            run.ended_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "ok": snap.get("error") is None,
            "native_nautilus": True,
            "recovered": recovered,
            "health": {
                "orders": len(snap.get("orders") or []),
                "fills": len(snap.get("fills") or []),
                "position_side": snap.get("position_side"),
                "path": snap.get("path"),
                "error": snap.get("error"),
            },
        }
    except Exception as exc:  # noqa: BLE001
        run = db.get(PaperRun, run_id)
        if run is not None:
            run.status = PaperRunStatus.FAILED.value
            run.failure_reason = str(exc)[:500]
            db.commit()
        return {"error": str(exc), "native_nautilus": False}
    finally:
        if close_db:
            db.close()


# Back-compat alias used by paper_run_service tests
def run_ticks(run_id: uuid.UUID, *, ticks: int = 5, sleep: float = 0.0, db=None) -> dict:
    seconds = max(3.0, min(12.0, ticks * 0.15 + 2.0))
    return run_nautilus(run_id, seconds=seconds, db=db)


def main() -> int:
    parser = argparse.ArgumentParser(description="QuantLab Nautilus paper-runner")
    parser.add_argument("run_id", help="PaperRun UUID")
    parser.add_argument("--once", action="store_true", help="Run timed window then exit")
    parser.add_argument("--seconds", type=float, default=8.0, help="TradingNode run window")
    parser.add_argument("--ticks", type=int, default=80, help="Legacy alias → seconds mapping")
    args = parser.parse_args()

    seconds = args.seconds if args.once else args.seconds
    if args.ticks and args.ticks != 80:
        seconds = max(3.0, min(12.0, args.ticks * 0.1 + 2.0))

    out = run_nautilus(uuid.UUID(args.run_id), seconds=seconds)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

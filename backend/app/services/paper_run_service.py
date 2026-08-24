"""PaperRun orchestration service."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.paper_run import (
    PaperReadyRegistry,
    PaperRun,
    PaperRunEvent,
    PaperRunFill,
    PaperRunOrder,
    PaperRunPosition,
    PaperRunStatus,
    SignalDecisionRecord,
)
from backend.app.models.user import User
from engine.paper.evaluation import build_paper_evaluation
from engine.paper.manifest import build_run_manifest
from engine.paper.paper_entry_gate import run_paper_entry_gate
from engine.paper.risk_policy import PaperRiskPolicy
from engine.paper.portfolio import portfolio_from_snapshot
from engine.strategies import validate_spec
from engine.strategies.compiler import compile_spec
from engine.strategies.runtime_params import require_nautilus_runtime_params
from engine.trading.execution_environment import EnvironmentGateError, assert_environment_allowed


class PaperRunError(Exception):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _git_commit() -> str:
    try:
        import subprocess as sp

        out = sp.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_repo_root(),
            text=True,
            timeout=3,
        )
        return out.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _run_spec_backtest_metrics(spec_payload: dict[str, Any]) -> dict[str, Any]:
    """Nautilus backtest from compiled Strategy Spec (same params as Paper)."""
    compiled = compile_spec(spec_payload)
    runtime = require_nautilus_runtime_params(spec_payload)
    try:
        from engine.nautilus.availability import nautilus_available
        from engine.nautilus.backtest_adapter import NautilusBacktestAdapter

        if not nautilus_available():
            return {"from_spec_backtest": False, "error": "nautilus_not_installed"}
        adapter = NautilusBacktestAdapter()
        result = adapter.run_compiled_ema(
            compiled.nautilus_params,
            strategy_id=compiled.source_spec_id,
            strategy_version=compiled.source_spec_version,
        )
        m = dict(result.metrics or {})
        m.update(
            {
                "from_spec_backtest": True,
                "signals_total": result.fill_count,
                "fill_count": result.fill_count,
                "orders_total": result.fill_count,
                "pnl": float(m.get("pnl") or m.get("total_pnl") or 0),
                "return_pct": float(m.get("return_pct") or 0),
                "max_drawdown": float(m.get("max_drawdown") or 0),
                "win_rate": float(m.get("win_rate") or 0),
                "fast_ema": runtime["ema_fast"],
                "slow_ema": runtime["ema_slow"],
            }
        )
        return m
    except Exception as exc:  # noqa: BLE001
        return {"from_spec_backtest": False, "error": str(exc)[:200]}


def register_paper_ready(
    db: Session,
    user: User,
    *,
    spec_payload: dict[str, Any],
    compiled_hash: str,
    data_gate_status: str,
    backtest_pass: bool,
    validation_pass: bool,
    robustness_pass: bool,
) -> PaperReadyRegistry:
    spec = validate_spec(spec_payload)
    gate = run_paper_entry_gate(
        strategy_spec_id=spec.strategy.id,
        strategy_spec_version=spec.strategy.version,
        strategy_spec_hash=spec.content_hash(),
        data_gate_status=data_gate_status,
        backtest_pass=backtest_pass,
        validation_pass=validation_pass,
        robustness_pass=robustness_pass,
        paper_ready_version=spec.strategy.version,
        paper_ready_hash=spec.content_hash(),
    )
    if gate.status != "PASS":
        raise PaperRunError("；".join(gate.detail_zh))

    row = PaperReadyRegistry(
        user_id=user.id,
        strategy_spec_id=spec.strategy.id,
        strategy_spec_version=spec.strategy.version,
        strategy_spec_hash=spec.content_hash(),
        compiled_strategy_hash=compiled_hash,
        gates=gate.checks,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_paper_run(
    db: Session,
    user: User,
    *,
    spec_payload: dict[str, Any],
    compiled_hash: str,
    environment: str = "SANDBOX",
    instrument: str = "BTCUSDT",
    data_provider: str = "synthetic",
    starting_balance: float = 100_000.0,
) -> PaperRun:
    settings = get_settings()
    if settings.quantlab_live:
        raise PaperRunError("LIVE=DENY")
    env = assert_environment_allowed(environment, layer="backend", live_allowed=False)

    spec = validate_spec(spec_payload)
    spec_hash = spec.content_hash()

    ready = db.execute(
        select(PaperReadyRegistry)
        .where(
            PaperReadyRegistry.user_id == user.id,
            PaperReadyRegistry.strategy_spec_id == spec.strategy.id,
            PaperReadyRegistry.strategy_spec_version == spec.strategy.version,
            PaperReadyRegistry.strategy_spec_hash == spec_hash,
        )
        .order_by(PaperReadyRegistry.created_at.desc())
    ).scalar_one_or_none()
    if ready is None:
        raise PaperRunError(
            f"策略 {spec.strategy.id}@{spec.strategy.version} 尚未 PAPER_READY，请先完成研究 Gate。"
        )

    policy = PaperRiskPolicy()
    runtime = require_nautilus_runtime_params(spec_payload)
    backtest_metrics = _run_spec_backtest_metrics(spec_payload)

    manifest = build_run_manifest(
        strategy_spec_id=spec.strategy.id,
        strategy_spec_version=spec.strategy.version,
        strategy_spec_hash=spec_hash,
        compiled_strategy_hash=compiled_hash or ready.compiled_strategy_hash,
        data_provider=data_provider,
        instrument=runtime["instrument"],
        venue="BINANCE",
        risk_policy_hash=policy.policy_hash(),
        application_commit=_git_commit(),
        environment=env.value,
    )

    effective = {
        **runtime,
        "spec": spec_payload,
        "compiled_hash": compiled_hash or ready.compiled_strategy_hash,
        "backtest_metrics": backtest_metrics,
        "synthetic_ticks": 80,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "runtime": "NAUTILUS_TRADING_NODE",
        "official_execution_path": "NAUTILUSTRADER",
    }

    run = PaperRun(
        user_id=user.id,
        strategy_spec_id=spec.strategy.id,
        strategy_spec_version=spec.strategy.version,
        strategy_spec_hash=spec_hash,
        compiled_strategy_hash=compiled_hash or ready.compiled_strategy_hash,
        environment=env.value,
        instrument=runtime["instrument"],
        venue="BINANCE",
        data_provider=data_provider,
        starting_balance=starting_balance,
        currency="USDT",
        simulated_balance=True,
        risk_policy_id=policy.policy_id,
        risk_policy_version=policy.version,
        risk_policy_hash=policy.policy_hash(),
        status=PaperRunStatus.CREATED.value,
        current_balance=starting_balance,
        run_manifest=manifest.to_dict(),
        run_manifest_hash=manifest.manifest_hash(),
        effective_config=effective,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def start_paper_run(db: Session, user_id: uuid.UUID, run_id: uuid.UUID) -> PaperRun:
    run = db.get(PaperRun, run_id)
    if run is None or run.user_id != user_id:
        raise PaperRunError("PaperRun 不存在")
    if run.status not in {PaperRunStatus.CREATED.value, PaperRunStatus.STOPPED.value, PaperRunStatus.FAILED.value}:
        raise PaperRunError(f"当前状态 {run.status} 不可启动")

    settings = get_settings()
    assert_environment_allowed(run.environment, layer="backend", live_allowed=False)
    run.status = PaperRunStatus.STARTING.value
    run.restart_count = int(run.restart_count or 0) + (1 if run.started_at else 0)
    db.commit()

    tick_count = 3 if run.data_provider == "synthetic" else 5

    if settings.celery_task_always_eager:
        from scripts.paper_runner import run_ticks

        out = run_ticks(run.id, ticks=tick_count, sleep=0, db=db)
        if out.get("error"):
            run.status = PaperRunStatus.FAILED.value
            run.failure_reason = str(out.get("error"))[:500]
        else:
            run.status = PaperRunStatus.STOPPED.value
            run.stop_reason = "tick_batch_complete"
            run.ended_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        _finalize_run_evaluation(db, run)
        db.refresh(run)
        return run

    script = _repo_root() / "scripts" / "paper_runner.py"
    cmd = [sys.executable, str(script), str(run.id), "--once", f"--ticks={tick_count}"]
    try:
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            cwd=str(_repo_root()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate(timeout=120)
        run.runner_pid = proc.pid
        if proc.returncode != 0:
            run.status = PaperRunStatus.FAILED.value
            run.failure_reason = (stderr or stdout or "runner failed")[:500]
        else:
            run.status = PaperRunStatus.STOPPED.value
            run.stop_reason = "tick_batch_complete"
            run.ended_at = datetime.now(timezone.utc)
        db.refresh(run)
        _finalize_run_evaluation(db, run)
        db.refresh(run)
        return run
    except subprocess.TimeoutExpired as exc:
        run.status = PaperRunStatus.FAILED.value
        run.failure_reason = "paper-runner timeout"
        db.commit()
        raise PaperRunError("paper-runner 超时") from exc


def stop_paper_run(db: Session, user_id: uuid.UUID, run_id: uuid.UUID) -> PaperRun:
    run = db.get(PaperRun, run_id)
    if run is None or run.user_id != user_id:
        raise PaperRunError("PaperRun 不存在")
    run.status = PaperRunStatus.STOPPING.value
    db.commit()
    run.status = PaperRunStatus.STOPPED.value
    run.stop_reason = "user_stop"
    run.ended_at = datetime.now(timezone.utc)
    db.commit()
    _finalize_run_evaluation(db, run)
    db.refresh(run)
    return run


def kill_paper_run(db: Session, user_id: uuid.UUID, run_id: uuid.UUID) -> PaperRun:
    run = db.get(PaperRun, run_id)
    if run is None or run.user_id != user_id:
        raise PaperRunError("PaperRun 不存在")
    run.kill_switch_active = True
    run.status = PaperRunStatus.KILLED.value
    run.stop_reason = "paper_run_kill_switch"
    run.ended_at = datetime.now(timezone.utc)
    db.commit()
    _finalize_run_evaluation(db, run)
    db.refresh(run)
    return run


def _finalize_run_evaluation(db: Session, run: PaperRun) -> None:
    """Attach performance summary + backtest comparison + research feedback."""
    comparison = backtest_vs_paper_report(db, run.user_id, run.id)
    perf = dict((run.metrics or {}).get("performance_summary") or {})
    evaluation = build_paper_evaluation(
        strategy_spec_id=run.strategy_spec_id,
        strategy_spec_version=run.strategy_spec_version,
        paper_run_id=str(run.id),
        performance_summary=perf,
        comparison=comparison,
        parity_status=str(comparison.get("parity_status") or "INVALID_COMPARISON"),
        run_status=run.status,
        failure_reason=run.failure_reason or "",
        data_stale=bool(run.data_stale),
    )
    metrics = dict(run.metrics or {})
    metrics["paper_evaluation"] = evaluation.to_dict()
    metrics["parity_status"] = comparison.get("parity_status")
    run.metrics = metrics
    db.add(
        PaperRunEvent(
            paper_run_id=run.id,
            code="PAPER_EVALUATION",
            message_zh="；".join(evaluation.research_feedback_zh[:3]),
            payload=evaluation.to_dict(),
        )
    )
    db.commit()


def paper_run_dashboard(db: Session, user_id: uuid.UUID, run_id: uuid.UUID) -> dict[str, Any]:
    run = db.get(PaperRun, run_id)
    if run is None or run.user_id != user_id:
        raise PaperRunError("PaperRun 不存在")

    orders = db.scalars(
        select(PaperRunOrder).where(PaperRunOrder.paper_run_id == run.id).order_by(PaperRunOrder.created_at.desc())
    ).all()
    fills = db.scalars(select(PaperRunFill).where(PaperRunFill.paper_run_id == run.id)).all()
    positions = db.scalars(
        select(PaperRunPosition).where(PaperRunPosition.paper_run_id == run.id)
    ).all()
    signals = db.scalars(
        select(SignalDecisionRecord)
        .where(SignalDecisionRecord.paper_run_id == run.id)
        .order_by(SignalDecisionRecord.decided_at.desc())
        .limit(20)
    ).all()

    uptime = ""
    if run.started_at:
        delta = (run.ended_at or datetime.now(timezone.utc)) - run.started_at
        hours = int(delta.total_seconds() // 3600)
        days = hours // 24
        uptime = f"{days}天 {hours % 24}小时" if days else f"{hours}小时"

    last_age = run.market_data_age_seconds
    last_quote = f"{last_age:.0f}秒前" if last_age is not None else "—"
    metrics = dict(run.metrics or {})
    perf = metrics.get("performance_summary") or {}
    equity = float(metrics.get("equity") or run.current_balance or 0)
    evaluation = metrics.get("paper_evaluation") or {}
    comparison = backtest_vs_paper_report(db, user_id, run.id)

    return {
        "id": str(run.id),
        "title_zh": "模拟交易",
        "disclaimer_zh": "模拟交易，不涉及真实资金",
        "strategy_name": run.strategy_spec_id,
        "strategy_version": run.strategy_spec_version,
        "status_zh": _status_zh(run.status),
        "uptime_zh": uptime or "—",
        "simulated_balance_zh": f"{float(run.current_balance):,.0f} {run.currency}",
        "starting_balance_zh": f"{float(run.starting_balance):,.0f} {run.currency}",
        "today_pnl_zh": f"{float(run.realized_pnl):+,.0f} {run.currency}",
        "total_pnl_zh": f"{float(metrics.get('net_pnl', run.realized_pnl) or 0):+,.0f} {run.currency}",
        "equity_zh": f"{equity:,.2f} {run.currency}",
        "unrealized_pnl_zh": f"{float(metrics.get('unrealized_pnl') or 0):+,.2f} {run.currency}",
        "max_drawdown_zh": f"{float(perf.get('max_drawdown') or 0) * 100:.2f}%",
        "position_zh": _position_zh(run),
        "risk_zh": "暂停" if run.risk_paused else "正常",
        "data_connection_zh": "异常" if run.data_stale else "正常",
        "last_quote_zh": last_quote,
        "alert_count": len(run.alerts or []),
        "environment": run.environment,
        "instrument": run.instrument,
        "orders_count": len(orders),
        "fills_count": len(fills),
        "positions_count": len(positions),
        "recent_signals": [
            {
                "decision": s.decision,
                "reason": s.reason,
                "conditions": s.conditions,
                "condition_values": s.condition_values,
                "decided_at": s.decided_at.isoformat(),
            }
            for s in signals
        ],
        "orders_zh": [_order_zh(o) for o in orders[:10]],
        "fills_zh": [
            {
                "label_zh": f"{f.instrument.replace('USDT', '')}{'买' if f.side == 'buy' else '卖'}成交",
                "price": str(f.price),
                "quantity": str(f.quantity),
                "fee_zh": f"手续费（模拟）{float(f.fee):.4f}",
            }
            for f in fills[:10]
        ],
        "performance_summary": perf,
        "equity_curve": metrics.get("equity_curve") or [],
        "parity_status": comparison.get("parity_status"),
        "research_feedback_zh": evaluation.get("research_feedback_zh") or [],
        "backtest_vs_paper_zh": comparison.get("summary_zh", []),
        "data_provider": run.data_provider,
        "official_execution_path": "NAUTILUSTRADER",
    }


def _status_zh(status: str) -> str:
    mapping = {
        "CREATED": "已创建",
        "STARTING": "启动中",
        "RUNNING": "正在模拟",
        "PAUSED": "已暂停",
        "STOPPING": "停止中",
        "STOPPED": "已停止",
        "FAILED": "失败",
        "KILLED": "已终止",
    }
    return mapping.get(status, status)


def _position_zh(run: PaperRun) -> str:
    if not run.position_side or float(run.position_qty or 0) <= 0:
        return "无持仓"
    side = "多单" if run.position_side == "long" else "空单"
    sym = run.instrument.replace("USDT", "")
    return f"{sym} {side}"


def _order_zh(order: PaperRunOrder) -> dict[str, str]:
    sym = order.instrument.replace("USDT", "")
    if order.status == "OrderFilled":
        label = f"{sym}{'买单' if order.side == 'buy' else '卖单'}已成交"
    elif order.status == "Rejected":
        label = f"{sym}订单被拒绝"
    elif order.status == "Canceled":
        label = f"{sym}订单已取消"
    else:
        label = f"{sym}订单{order.status}"
    return {
        "label_zh": label,
        "time": order.created_at.isoformat(),
        "price": str(order.price or "—"),
        "quantity": str(order.quantity),
        "fee_zh": "手续费（模拟）",
        "strategy": order.signal_reason or "—",
        "trigger_reason": order.signal_reason or "—",
    }


def paper_run_to_dict(run: PaperRun) -> dict[str, Any]:
    return {
        "id": str(run.id),
        "strategy_spec_id": run.strategy_spec_id,
        "strategy_spec_version": run.strategy_spec_version,
        "environment": run.environment,
        "instrument": run.instrument,
        "status": run.status,
        "simulated_balance": run.simulated_balance,
        "starting_balance": float(run.starting_balance),
        "current_balance": float(run.current_balance),
        "realized_pnl": float(run.realized_pnl),
        "data_gate_status": run.data_gate_status,
        "data_stale": run.data_stale,
        "run_manifest_hash": run.run_manifest_hash,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
    }


def backtest_vs_paper_report(db: Session, user_id: uuid.UUID, run_id: uuid.UUID) -> dict[str, Any]:
    run = db.get(PaperRun, run_id)
    if run is None or run.user_id != user_id:
        raise PaperRunError("PaperRun 不存在")

    from engine.paper.backtest_compare import build_backtest_paper_report

    eff = run.effective_config or {}
    bt = (eff.get("backtest_metrics") or {}) if isinstance(eff, dict) else {}
    paper_metrics = dict(run.metrics or {})
    perf = paper_metrics.get("performance_summary") or {}
    paper_metrics["realized_pnl"] = float(run.realized_pnl or 0)
    paper_metrics["position_qty"] = float(run.position_qty or 0)
    paper_metrics["return_pct"] = float(perf.get("return_pct") or 0)
    paper_metrics["max_drawdown"] = float(perf.get("max_drawdown") or 0)
    paper_metrics["orders_total"] = int(paper_metrics.get("orders_total") or 0)
    paper_metrics["fills_total"] = int(paper_metrics.get("fills_total") or 0)
    report = build_backtest_paper_report(
        strategy_spec_id=run.strategy_spec_id,
        strategy_spec_version=run.strategy_spec_version,
        backtest_metrics=bt,
        paper_metrics=paper_metrics,
    )
    return report.to_dict()

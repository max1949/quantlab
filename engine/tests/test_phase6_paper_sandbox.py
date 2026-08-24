"""Phase 6 paper sandbox tests."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from engine.paper.gates import run_realtime_data_gate
from engine.paper.kill_switch import KillSwitchState, check_kill_switch
from engine.paper.market_data import SyntheticTickProvider
from engine.paper.paper_entry_gate import run_paper_entry_gate
from engine.paper.recovery import RecoverySnapshot, should_allow_new_entry
from engine.paper.risk_policy import PaperRiskPolicy, evaluate_risk
from engine.paper.sandbox_runtime import SandboxPaperRuntime, SandboxRuntimeConfig
from engine.trading.execution_environment import EnvironmentGateError, assert_environment_allowed


class MemoryStore:
    def __init__(self) -> None:
        self.status = "CREATED"
        self.kill = KillSwitchState()
        self.position_side = None
        self.position_qty = 0.0
        self.restart_count = 0
        self.rows: list[dict] = []

    def get_kill_state(self) -> KillSwitchState:
        return self.kill

    def get_recovery_snapshot(self) -> RecoverySnapshot:
        return RecoverySnapshot(
            has_open_position=bool(self.position_side and self.position_qty > 0),
            open_side=self.position_side,
            open_quantity=self.position_qty,
            recovered_from_crash=self.restart_count > 0,
            restart_count=self.restart_count,
        )

    def get_metrics(self) -> dict:
        return {}

    def mark_status(self, status: str, *, detail: str = "") -> None:
        self.status = status

    def persist_tick(self, **kwargs) -> None:
        self.rows.append(kwargs)
        self.position_side = kwargs.get("position_side")
        self.position_qty = kwargs.get("position_qty", 0.0)


def test_environment_gate_rejects_live():
    with pytest.raises(EnvironmentGateError):
        assert_environment_allowed("LIVE", layer="backend", live_allowed=False)


def test_phase6_allowed_environments():
    for env in ("BACKTEST", "SANDBOX", "PAPER", "SHADOW"):
        assert assert_environment_allowed(env).value == env


def test_paper_entry_gate_requires_version_match():
    ok = run_paper_entry_gate(
        strategy_spec_id="s1",
        strategy_spec_version="v7",
        strategy_spec_hash="hash7",
        data_gate_status="PASS",
        backtest_pass=True,
        validation_pass=True,
        robustness_pass=True,
        paper_ready_version="v7",
        paper_ready_hash="hash7",
    )
    assert ok.status == "PASS"
    bad = run_paper_entry_gate(
        strategy_spec_id="s1",
        strategy_spec_version="v8",
        strategy_spec_hash="hash8",
        data_gate_status="PASS",
        backtest_pass=True,
        validation_pass=True,
        robustness_pass=True,
        paper_ready_version="v7",
        paper_ready_hash="hash7",
    )
    assert bad.status == "FAIL"


def test_realtime_data_gate_stale():
    old = datetime.now(timezone.utc) - timedelta(seconds=120)
    gate = run_realtime_data_gate(
        last_event_ts=old,
        instrument_loaded=True,
        stream_active=True,
    )
    assert gate.status in {"FAIL", "WARN"}
    assert not gate.data_fresh


def test_kill_switch_denies():
    assert check_kill_switch(KillSwitchState(global_active=True)) == "DENY"


def test_restart_duplicate_entry_blocked():
    snap = RecoverySnapshot(
        has_open_position=True,
        open_side="long",
        open_quantity=0.1,
        recovered_from_crash=True,
        restart_count=1,
    )
    ok, msg = should_allow_new_entry(signal_side="long", snapshot=snap)
    assert not ok
    assert "重复" in msg


def test_risk_daily_loss_triggers_pause():
    pol = PaperRiskPolicy(daily_loss_limit=100)
    ev = evaluate_risk(
        pol,
        order_notional=1000,
        position_notional=0,
        open_positions=0,
        strategy_exposure=0,
        daily_pnl=-150,
        drawdown=0,
        consecutive_losses=0,
        orders_last_minute=0,
    )
    assert not ev.allowed
    assert ev.action == "PAUSE_STRATEGY"


def test_sandbox_runtime_ticks_with_synthetic_data():
    store = MemoryStore()
    cfg = SandboxRuntimeConfig(run_id=str(uuid.uuid4()), instrument="BTCUSDT", environment="SANDBOX")
    rt = SandboxPaperRuntime(
        config=cfg,
        store=store,
        market_data=SyntheticTickProvider(base_price=60_000, step=10),
    )
    for _ in range(5):
        rt.tick_once()
    assert len(store.rows) == 5
    assert rt.health()["environment"] == "SANDBOX"


def test_phase6_rejects_live_execution_client():
    with pytest.raises(EnvironmentGateError):
        SandboxPaperRuntime(
            config=SandboxRuntimeConfig(run_id="x", environment="LIVE"),
            store=MemoryStore(),
            market_data=SyntheticTickProvider(),
        )


def test_golden_btc_spec_loads():
    from engine.strategies import validate_spec
    import yaml

    path = Path(__file__).resolve().parents[2] / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    spec = validate_spec(yaml.safe_load(path.read_text(encoding="utf-8")))
    assert spec.market.instrument.replace("/", "").upper().startswith("BTC")

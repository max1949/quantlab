"""QLN-5 Paper Sandbox canonical closure tests (repair/merge/retire)."""

from __future__ import annotations

from pathlib import Path

from engine.paper.canonical import (
    PAPER_PATH_REGISTRY,
    PaperPathDisposition,
    canonical_paper_apis,
    soft_retired_paper_apis,
)
from engine.paper.evaluation import build_paper_evaluation
from engine.paper.kill_switch import KillSwitchState, check_kill_switch
from engine.paper.ledger_bridge import append_paper_evaluation_to_ledger
from engine.paper.recovery import RecoverySnapshot, should_allow_new_entry
from engine.paper.sandbox_runtime import PAPER_PATH_DISPOSITION
from engine.strategies.runtime_params import require_nautilus_runtime_params
from engine.strategies.validate import load_spec
from engine.strategies.v2.compiler import compile_spec_v2_deterministic
from engine.strategies.v2.migrate import migrate_v1_file_to_v2

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "strategy_specs" / "examples" / "golden_01_ema_trend.v1.yaml"


def test_canonical_registry_dispositions():
    assert PAPER_PATH_REGISTRY["paper_run"]["disposition"] == PaperPathDisposition.CANONICAL.value
    assert PAPER_PATH_REGISTRY["paper_orders"]["disposition"] == PaperPathDisposition.SOFT_RETIRE.value
    assert PAPER_PATH_REGISTRY["sandbox_runtime"]["disposition"] == PaperPathDisposition.SOFT_RETIRE.value
    assert "/paper-sandbox/*" in canonical_paper_apis()
    assert "/execution/paper/*" in soft_retired_paper_apis()
    assert PAPER_PATH_DISPOSITION == "SOFT_RETIRE"


def test_spec_to_runtime_params_parity_with_v2_adapter():
    v1 = load_spec(GOLDEN)
    rp = require_nautilus_runtime_params(v1)
    v2, _, _ = migrate_v1_file_to_v2(GOLDEN)
    c2 = compile_spec_v2_deterministic(v2)
    np = c2["nautilus_params"]
    assert rp["ema_fast"] == np["fast_ema"] == 10
    assert rp["ema_slow"] == np["slow_ema"] == 20
    assert str(rp["trade_size"]) == str(np["trade_size"])
    assert "EUR" in rp["instrument"].upper() or "EUR" in str(np["instrument"]).upper()


def test_kill_switch_denies_when_any_scope_active():
    assert check_kill_switch(KillSwitchState()) == "ALLOW"
    assert check_kill_switch(KillSwitchState(global_active=True)) == "DENY"
    assert check_kill_switch(KillSwitchState(paper_run_active=True)) == "DENY"
    assert check_kill_switch(KillSwitchState(strategy_active=True, reason="manual")) == "DENY"


def test_restart_recovery_blocks_duplicate_entry():
    snap = RecoverySnapshot(
        has_open_position=True,
        open_side="LONG",
        open_quantity=1.0,
        recovered_from_crash=True,
        restart_count=1,
    )
    ok, reason = should_allow_new_entry(signal_side="LONG", snapshot=snap)
    assert ok is False
    assert "禁止重复" in reason or "同向" in reason
    ok2, _ = should_allow_new_entry(signal_side="SHORT", snapshot=snap, allow_exit=True)
    assert ok2 is True


def test_paper_evaluation_appends_to_experiment_ledger(tmp_path):
    from engine.experiment.ledger import ExperimentLedger

    ev = build_paper_evaluation(
        strategy_spec_id="golden_01_ema_trend",
        strategy_spec_version="v1",
        paper_run_id="run-1",
        performance_summary={
            "trade_count": 5,
            "duration_seconds": 120,
            "net_pnl": 1.0,
            "max_drawdown": 0.01,
        },
        comparison={},
        parity_status="CONSISTENT",
        run_status="STOPPED",
    )
    ledger = ExperimentLedger(tmp_path / "exp.jsonl")
    rec = append_paper_evaluation_to_ledger(ev, ledger=ledger, dataset_hash="abc123")
    assert rec.evidence_stage == "E4_PAPER"
    assert ledger.get(rec.experiment_id) is not None


def test_live_route_deny_preserved_in_paper_registry():
    blob = str(PAPER_PATH_REGISTRY).upper()
    assert "LIVE_ROUTE=ALLOW" not in blob

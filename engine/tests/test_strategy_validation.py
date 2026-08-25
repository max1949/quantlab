"""Unit tests for Strategy Validation Gate (no LIVE / no Phase 7)."""

from __future__ import annotations

from engine.validation.decision import GateChecklist, assess_overfit_risk, decide_outcome
from engine.validation.graveyard import GraveyardEntry, append_reject, list_rejects


def test_decide_promote_requires_all_pass():
    gates = GateChecklist(
        oos="PASS",
        walk_forward="PASS",
        robustness="PASS",
        cost_stress="PASS",
        paper="PASS",
        parity="PASS",
    )
    r = decide_outcome(gates, overfit_risk="LOW")
    assert r.decision == "PROMOTE"


def test_decide_hold_when_paper_insufficient():
    gates = GateChecklist(
        oos="PASS",
        walk_forward="PASS",
        robustness="PASS",
        cost_stress="PASS",
        paper="INSUFFICIENT",
        parity="INSUFFICIENT",
    )
    r = decide_outcome(gates, overfit_risk="LOW")
    assert r.decision == "HOLD"


def test_decide_reject_on_oos_fail():
    gates = GateChecklist(
        oos="FAIL",
        walk_forward="PASS",
        robustness="PASS",
        cost_stress="PASS",
        paper="INSUFFICIENT",
        parity="INSUFFICIENT",
    )
    r = decide_outcome(gates, overfit_risk="MEDIUM")
    assert r.decision == "REJECT"


def test_profitable_backtest_alone_does_not_promote():
    # Empty / insufficient gates: never PROMOTE
    r = decide_outcome(GateChecklist(), overfit_risk="LOW")
    assert r.decision != "PROMOTE"


def test_overfit_high_blocks_promote():
    gates = GateChecklist(
        oos="PASS",
        walk_forward="PASS",
        robustness="PASS",
        cost_stress="PASS",
        paper="PASS",
        parity="PASS",
    )
    r = decide_outcome(gates, overfit_risk="HIGH")
    assert r.decision == "REJECT"


def test_graveyard_append(tmp_path):
    path = tmp_path / "rejects.jsonl"
    append_reject(
        GraveyardEntry(
            strategy_id="t1",
            strategy_version="v1",
            hypothesis="x",
            market="EUR/USD",
            timeframe="15m",
            validation_results={"oos": "FAIL"},
            failure_reason="OOS fail",
            rejected_at="",
        ),
        path=path,
    )
    rows = list_rejects(path=path)
    assert len(rows) == 1
    assert rows[0]["strategy_id"] == "t1"


def test_assess_overfit_knife_edge():
    risk = assess_overfit_risk(
        param_count=2,
        trade_count=10,
        periods=100,
        sens_positive_ratio=0.2,
        sharpe_degradation=0.8,
        wf_positive_ratio=0.3,
        top_win_concentration=0.7,
    )
    assert risk == "HIGH"

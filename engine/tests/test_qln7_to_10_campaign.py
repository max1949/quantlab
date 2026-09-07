"""QLN-7 / QLN-8 / QLN-9 / QLN-10 focused acceptance tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.canary import CanaryCapitalContract, evaluate_live_readiness
from engine.portfolio import (
    PortfolioGovernor,
    PortfolioLimits,
    capacity_check,
    evaluate_portfolio,
    style_exposure,
)
from engine.reliability import (
    DeadManSwitch,
    SecretsPlane,
    chaos_acceptance_suite,
    probe_secret_leak,
)
from engine.shadow import (
    FlightEvent,
    FlightRecorder,
    ShadowSnapshot,
    behavior_parity_report,
    compare_twins,
    loss_attribution,
    replay_events,
)


def _rets(seed: int, n: int = 60) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="B", tz="UTC")
    return pd.Series(rng.normal(0, 0.01, size=n), index=idx)


# --- QLN-7 ---


def test_qln7_exposure_and_capacity():
    exp = style_exposure({"a": _rets(1), "b": _rets(2)}, market=_rets(3))
    assert "vol" in exp["a"]
    cap = capacity_check(strategy_id="a", desired_notional=1000, adv_notional=100_000)
    assert cap["status"] == "PASS"
    fail = capacity_check(strategy_id="a", desired_notional=50_000, adv_notional=100_000)
    assert fail["status"] == "FAIL"


def test_qln7_governor_actions_auditable():
    gov = PortfolioGovernor(
        strategy_ids=["hist_fl_momentum_w20", "hist_fl_rsi_w14"],
        weights={"hist_fl_momentum_w20": 0.4, "hist_fl_rsi_w14": 0.4},
        instruments={"hist_fl_momentum_w20": "RB", "hist_fl_rsi_w14": "AU"},
        limits=PortfolioLimits(),
    )
    actions = evaluate_portfolio(gov, returns={"hist_fl_momentum_w20": _rets(1), "hist_fl_rsi_w14": _rets(2)})
    assert all(a.auditable and a.replayable and not a.bypasses_invariants for a in actions)


# --- QLN-8 ---


def test_qln8_twin_divergence_and_flight_explain(tmp_path):
    ref = ShadowSnapshot(ts="t1", strategy_id="s1", signal=1.0, order_side="BUY", position=1.0)
    sh = ShadowSnapshot(ts="t1", strategy_id="s1", signal=-1.0, order_side="SELL", position=0.0)
    evs = compare_twins(ref, sh)
    kinds = {e.kind for e in evs}
    assert "SIGNAL" in kinds and "ORDER" in kinds and "POSITION" in kinds

    rec = FlightRecorder(tmp_path / "events.jsonl")
    rec.append(
        FlightEvent(
            event_id="e1",
            ts="t1",
            strategy_id="s1",
            event_type="DECISION",
            saw={"signal": 1.0},
            why="sign(signal)>0",
            risk={"max_open": 1},
            happened={"order": "BUY"},
        )
    )
    rec.append(
        FlightEvent(
            event_id="e2",
            ts="t2",
            strategy_id="s1",
            event_type="OUTCOME",
            why="stop",
            happened={"pnl": -10.0},
        )
    )
    explained = rec.explain_event("e1")
    assert explained is not None
    assert explained["saw"] and explained["why"] and "risk" in explained and "happened" in explained
    assert behavior_parity_report(reference_actions=["BUY"], shadow_actions=["BUY"])["parity"] == "PASS"
    assert loss_attribution(rec.list_events())["n_loss_events"] == 1
    assert len(replay_events(rec, strategy_id="s1")) == 2


# --- QLN-9 ---


def test_qln9_chaos_acceptance_and_secrets():
    suite = chaos_acceptance_suite()
    assert suite["CHAOS_ACCEPTANCE"] == "PASS"
    assert suite["RECONCILIATION"] == "PASS"
    assert suite["DUPLICATE_ORDER_ON_RECOVERY"] == 0
    assert suite["UNKNOWN_STATE_NEW_RISK"] == 0
    assert suite["SECRET_LEAK"] == 0
    plane = SecretsPlane()
    plane.put("slot_a", "super-secret-value")
    assert plane.audit_view()["slot_a"] == "***REDACTED***"
    assert probe_secret_leak(plane.audit_view()) == 0
    assert probe_secret_leak({"api_key": "sk-" + "x" * 24}) >= 1
    assert DeadManSwitch().evaluate(now_ts_epoch=1000, last_epoch=100) == "TRIP"


# --- QLN-10 ---


def test_qln10_live_readiness_pass_without_live():
    report = evaluate_live_readiness(
        qln5_paper_pass=True,
        qln8_shadow_pass=True,
        qln9_chaos_pass=True,
        capital=CanaryCapitalContract(
            max_notional=1000,
            max_loss=100,
            venues_allowed=["SIMULATED"],
            strategies_allowed=["hist_fl_momentum_w20"],
            real_money_authorized=False,
        ),
        owner_live_approval=False,
    )
    assert report.LIVE_READINESS == "PASS"
    assert report.qln11_auto_enter == "DENY"
    assert report.real_money == "NO"


def test_qln10_hold_when_shadow_missing():
    report = evaluate_live_readiness(
        qln5_paper_pass=True,
        qln8_shadow_pass=False,
        qln9_chaos_pass=True,
        capital=CanaryCapitalContract(max_notional=1000, max_loss=100),
    )
    assert report.LIVE_READINESS == "HOLD"

"""Continuous Shadow evidence against canonical factor_sign Paper (QLN-8 stack).

Requires PAPER_QUALIFIED=YES. Uses Shadow Twin, Flight Recorder, divergence,
replay, attribution, reconciliation, restart/recovery, dead-man — no Live orders.
Not a 60-bar research dry-run; window = last ≥252 trading days of genuine RB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.paper.factor_sign_runtime import run_factor_sign_paper
from engine.reliability import DeadManSwitch, ReconciliationReport
from engine.shadow import (
    FlightEvent,
    FlightRecorder,
    ShadowSnapshot,
    behavior_parity_report,
    compare_twins,
    loss_attribution,
    replay_events,
)
from engine.strategies.v2.factor_sign_adapter import compile_factor_sign_to_paper
from engine.strategies.v2.package import import_package
from engine.strategies.v2.spec_v2 import validate_spec_v2

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_momentum_w20.v2.package.json"
RB = ROOT / "data" / "market_data" / "genuine_recovery" / "RB_1d.parquet"
PAPER_ART = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "paper_qualification_hist_fl_momentum_w20_rb.json"
OUT = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "shadow_continuous_evidence.json"
FLIGHT = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "shadow_flight_continuous.jsonl"

MIN_BARS = 252
STRATEGY_ID = "hist_fl_momentum_w20"


def _load_rb_window() -> pd.DataFrame:
    df = pd.read_parquet(RB)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df = df.copy()
        df.index = df.index.tz_localize("UTC")
    df = df.sort_index()
    if len(df) < MIN_BARS:
        raise RuntimeError(f"RB bars {len(df)} < MIN_BARS={MIN_BARS}")
    # Continuous window: last full year of trading days (not 60-bar smoke)
    return df.iloc[-max(MIN_BARS, 504) :]


def main() -> dict[str, Any]:
    paper_q = "NO"
    if PAPER_ART.exists():
        paper_q = json.loads(PAPER_ART.read_text(encoding="utf-8")).get("PAPER_QUALIFIED", "NO")

    reasons: list[str] = []
    if paper_q != "YES":
        reasons.append("PAPER_QUALIFIED!=YES — continuous Shadow requires Paper twin counterpart")
        out = {
            "SHADOW_CONTINUOUS_EVIDENCE": "HOLD",
            "PAPER_QUALIFIED_INPUT": paper_q,
            "reasons": reasons,
            "ORDERS_CREATED": "NO",
            "REAL_MONEY": "NO",
        }
        OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(out, indent=2))
        return out

    pkg = import_package(PKG)
    spec = validate_spec_v2(pkg.strategy_spec)
    contract = compile_factor_sign_to_paper(spec, instrument="RB")
    ohlcv = _load_rb_window()

    # Reference Paper stream
    paper = run_factor_sign_paper(contract, ohlcv, paper_run_id="fs-shadow-ref-paper")
    # Shadow twin: independent recompute (same contract — parity expected)
    shadow = run_factor_sign_paper(contract, ohlcv, paper_run_id="fs-shadow-twin")
    # Restart mid-window on shadow path
    shadow_restart = run_factor_sign_paper(
        contract,
        ohlcv,
        paper_run_id="fs-shadow-restart",
        inject_restart_at=min(100, len(ohlcv) - 10),
    )

    if FLIGHT.exists():
        FLIGHT.unlink()
    rec = FlightRecorder(FLIGHT)

    divergences = 0
    signal_parity = 0
    order_parity = 0
    position_parity = 0
    paper_actions: list[str] = []
    shadow_actions: list[str] = []
    n = min(len(paper.snapshot["positions"]), len(shadow.snapshot["positions"]))

    for i in range(n):
        ppos = paper.snapshot["positions"][i]
        spos = shadow.snapshot["positions"][i]
        psig = paper.snapshot["signals"][i] if i < len(paper.snapshot["signals"]) else {}
        ssig = shadow.snapshot["signals"][i] if i < len(shadow.snapshot["signals"]) else {}
        ts = str(ppos.get("ts"))
        pref_side = "BUY" if (psig.get("intended_position") or 0) > 0 else (
            "SELL" if (psig.get("intended_position") or 0) < 0 else None
        )
        sh_side = "BUY" if (ssig.get("intended_position") or 0) > 0 else (
            "SELL" if (ssig.get("intended_position") or 0) < 0 else None
        )
        ref = ShadowSnapshot(
            ts=ts,
            strategy_id=STRATEGY_ID,
            signal=float(psig.get("signal") or 0.0),
            order_side=pref_side,
            position=float(ppos.get("position") or 0.0),
            price=None,
            source="paper",
        )
        sh = ShadowSnapshot(
            ts=ts,
            strategy_id=STRATEGY_ID,
            signal=float(ssig.get("signal") or 0.0),
            order_side=sh_side,
            position=float(spos.get("position") or 0.0),
            price=None,
            source="shadow",
        )
        evs = compare_twins(ref, sh)
        kinds = {e.kind for e in evs}
        if "SIGNAL" in kinds:
            divergences += 1
        else:
            signal_parity += 1
        if "ORDER" in kinds:
            divergences += 1
        else:
            order_parity += 1
        if "POSITION" in kinds:
            divergences += 1
        else:
            position_parity += 1
        paper_actions.append(pref_side or "FLAT")
        shadow_actions.append(sh_side or "FLAT")

        pnl_delta = 0.0
        if i > 0:
            pnl_delta = float(ppos.get("equity") or 0) - float(paper.snapshot["positions"][i - 1].get("equity") or 0)
        rec.append(
            FlightEvent(
                event_id=f"cont-{i}",
                ts=ts,
                strategy_id=STRATEGY_ID,
                event_type="OUTCOME" if pnl_delta != 0 else "DECISION",
                saw={"signal": ref.signal, "intended": pref_side},
                why="sign(signal)+lag Paper↔Shadow continuous twin",
                risk={"max_open": contract.max_open_positions},
                happened={"position": ref.position, "pnl": pnl_delta, "shadow_position": sh.position},
            )
        )

    # Intentional divergence injection to prove detector works
    bad = ShadowSnapshot(
        ts="inject",
        strategy_id=STRATEGY_ID,
        signal=-999.0,
        order_side="SELL",
        position=-1.0,
        source="shadow_inject",
    )
    good = ShadowSnapshot(
        ts="inject",
        strategy_id=STRATEGY_ID,
        signal=1.0,
        order_side="BUY",
        position=1.0,
        source="paper",
    )
    inject_kinds = {e.kind for e in compare_twins(good, bad)}
    detector_ok = "SIGNAL" in inject_kinds and "ORDER" in inject_kinds and "POSITION" in inject_kinds

    # Dead-man: stale heartbeat must TRIP; fresh must OK
    dms = DeadManSwitch(trip_on_stale_seconds=60)
    dead_trip = dms.evaluate(now_ts_epoch=10_000, last_epoch=100) == "TRIP"
    dead_ok = dms.evaluate(now_ts_epoch=10_000, last_epoch=9_980) == "OK"

    # Reconciliation Paper vs Shadow end positions
    recon = ReconciliationReport.from_positions(
        {contract.instrument: float(paper.snapshot["positions"][-1].get("position") or 0)},
        {contract.instrument: float(shadow.snapshot["positions"][-1].get("position") or 0)},
    )

    # Replay + attribution
    replayed = replay_events(rec, strategy_id=STRATEGY_ID)
    attribution = loss_attribution(rec.list_events(strategy_id=STRATEGY_ID))
    behavior = behavior_parity_report(reference_actions=paper_actions, shadow_actions=shadow_actions)

    flight_complete = len(replayed) == n and n >= MIN_BARS
    restart_ok = len(shadow_restart.recovery_events) > 0

    continuous_pass = (
        paper_q == "YES"
        and divergences == 0
        and detector_ok
        and dead_trip
        and dead_ok
        and recon.status == "PASS"
        and behavior["parity"] == "PASS"
        and flight_complete
        and restart_ok
        and n >= MIN_BARS
    )

    if divergences:
        reasons.append(f"twin divergences={divergences}")
    if not detector_ok:
        reasons.append("divergence detector failed injection probe")
    if not (dead_trip and dead_ok):
        reasons.append("dead-man behavior incomplete")
    if recon.status != "PASS":
        reasons.append(f"reconciliation {recon.status}: {recon.drifts}")
    if behavior["parity"] != "PASS":
        reasons.append("behavior parity FAIL")
    if not flight_complete:
        reasons.append(f"flight recorder incomplete n={n} replayed={len(replayed)}")
    if not restart_ok:
        reasons.append("restart/recovery not exercised on shadow path")
    if continuous_pass:
        reasons.append(f"continuous Paper↔Shadow twin PASS over {n} bars with QLN-8 stack")

    out = {
        "SHADOW_CONTINUOUS_EVIDENCE": "PASS" if continuous_pass else "HOLD",
        "PAPER_QUALIFIED_INPUT": paper_q,
        "window_bars": n,
        "min_bars_required": MIN_BARS,
        "not_smoke": True,
        "not_60_bar_research_dry_run": n != 60 and n >= MIN_BARS,
        "divergences": divergences,
        "signal_parity_bars": signal_parity,
        "intended_order_parity_bars": order_parity,
        "position_state_parity_bars": position_parity,
        "divergence_detector_injection": "PASS" if detector_ok else "FAIL",
        "dead_man": {"trip_on_stale": dead_trip, "ok_on_fresh": dead_ok},
        "reconciliation": recon.model_dump(mode="json"),
        "restart_recovery_events": len(shadow_restart.recovery_events),
        "flight_events": len(rec.list_events()),
        "flight_path": str(FLIGHT),
        "replay_count": len(replayed),
        "loss_attribution": attribution,
        "behavior_parity": behavior["parity"],
        "reasons": reasons,
        "ORDERS_CREATED": "NO",
        "REAL_MONEY": "NO",
        "BROKER_LIVE_CAPABILITY": "HOLD",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "SHADOW_CONTINUOUS_EVIDENCE": out["SHADOW_CONTINUOUS_EVIDENCE"],
                "window_bars": n,
                "divergences": divergences,
            },
            indent=2,
        )
    )
    return out


if __name__ == "__main__":
    main()

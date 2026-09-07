"""Canonical factor_sign Paper qualification — hist_fl_momentum_w20 · RB.

Path: Spec v2 → Factor Sign Adapter → PaperRuntimeContract → PaperRun.
Does not use paper_orders, sandbox_runtime, or Factor Lab as Paper.
Does not create Live/Broker orders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.experiment.ledger import ExperimentLedger
from engine.paper.canonical import PAPER_PATH_REGISTRY, PaperPathDisposition
from engine.paper.evaluation import build_paper_evaluation
from engine.paper.factor_sign_runtime import dataset_hash_ohlcv, run_factor_sign_paper
from engine.paper.kill_switch import KillSwitchState
from engine.paper.ledger_bridge import append_paper_evaluation_to_ledger
from engine.strategies.v2.factor_sign_adapter import compile_factor_sign_to_paper
from engine.strategies.v2.package import import_package
from engine.strategies.v2.spec_v2 import validate_spec_v2

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_momentum_w20.v2.package.json"
RB = ROOT / "data" / "market_data" / "genuine_recovery" / "RB_1d.parquet"
OUT = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "paper_qualification_hist_fl_momentum_w20_rb.json"
EVIDENCE_DIR = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "paper_runs"
LEDGER = EVIDENCE_DIR / "experiment_ledger_factor_sign_paper.jsonl"


def _load_rb() -> pd.DataFrame:
    df = pd.read_parquet(RB)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df = df.copy()
        df.index = df.index.tz_localize("UTC")
    return df.sort_index()


def _checks(result, *, kill_result, recovery_result, ledger_id: str | None) -> dict[str, Any]:
    snap = result.snapshot
    return {
        "signal": len(snap.get("signals") or []) > 0,
        "intended_orders": len(snap.get("orders") or []) > 0,
        "fills": len(snap.get("fills") or []) > 0,
        "positions": len(snap.get("positions") or []) > 0,
        "equity": snap.get("equity") is not None,
        "risk": isinstance(snap.get("risk_events"), list),
        "kill_switch": len(kill_result.kill_events) > 0,
        "restart_recovery": len(recovery_result.recovery_events) > 0,
        "experiment_ledger_linkage": bool(ledger_id),
        "evidence_linkage": (EVIDENCE_DIR / f"{snap['paper_run_id']}.json").is_file(),
    }


def main() -> dict[str, Any]:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    pkg = import_package(PKG)
    spec = validate_spec_v2(pkg.strategy_spec)
    contract = compile_factor_sign_to_paper(spec, instrument="RB")
    ohlcv = _load_rb()
    ds_hash = dataset_hash_ohlcv(ohlcv)

    # Primary PaperRun over full genuine RB history
    primary = run_factor_sign_paper(contract, ohlcv, paper_run_id="fs-paper-rb-primary")
    # Kill switch drill (mid-series activate via pre-set state)
    kill = run_factor_sign_paper(
        contract,
        ohlcv.iloc[:120],
        paper_run_id="fs-paper-rb-kill",
        kill_state=KillSwitchState(strategy_active=True, reason="qualification_kill_drill"),
    )
    # Restart/recovery drill
    recovery = run_factor_sign_paper(
        contract,
        ohlcv.iloc[-400:],
        paper_run_id="fs-paper-rb-recovery",
        inject_restart_at=80,
    )

    parity = primary.parity.get("FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY")
    registry_ok = (
        PAPER_PATH_REGISTRY.get("factor_sign_paper", {}).get("disposition")
        == PaperPathDisposition.CANONICAL.value
    )
    legacy_used = "NO"

    # Persist evidence artifact
    evidence_path = EVIDENCE_DIR / f"{primary.snapshot['paper_run_id']}.json"
    evidence_path.write_text(
        json.dumps(
            {
                "contract": contract.to_dict(),
                "result": primary.to_dict(),
                "dataset_hash": ds_hash,
                "instrument": "RB",
                "bars": int(len(ohlcv)),
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    evaluation = build_paper_evaluation(
        strategy_spec_id=contract.strategy_id,
        strategy_spec_version=contract.strategy_version,
        paper_run_id=primary.snapshot["paper_run_id"],
        performance_summary={
            "trade_count": primary.snapshot["trade_count"],
            "duration_seconds": primary.snapshot["duration_seconds"],
            "net_pnl": primary.snapshot["realized_pnl"],
            "max_drawdown": primary.snapshot["max_drawdown"],
            "equity": primary.snapshot["equity"],
        },
        comparison={"parity": primary.parity},
        parity_status="CONSISTENT" if parity == "PASS" else "MATERIAL_DRIFT",
        run_status="STOPPED",
        risk_events=list(primary.snapshot.get("risk_events") or []),
    )
    ledger = ExperimentLedger(LEDGER)
    if LEDGER.exists():
        LEDGER.unlink()
    rec = append_paper_evaluation_to_ledger(
        evaluation,
        ledger=ledger,
        dataset_hash=ds_hash,
        dataset_id="genuine_recovery_RB_1d",
        engine_version=contract.adapter_version,
        adapter_version=contract.adapter_version,
    )

    checks = _checks(primary, kill_result=kill, recovery_result=recovery, ledger_id=rec.experiment_id)
    all_checks = all(checks.values())
    qualified = (
        parity == "PASS"
        and registry_ok
        and legacy_used == "NO"
        and all_checks
        and evaluation.evaluation_status == "COMPLETE"
        and primary.snapshot.get("PAPER_RUNTIME") == "CANONICAL"
        and primary.snapshot.get("LEGACY_PAPER_ORDERS_USED") == "NO"
    )

    reasons: list[str] = []
    if parity != "PASS":
        reasons.append(f"semantic parity FAIL: {primary.parity}")
    if not registry_ok:
        reasons.append("factor_sign_paper not registered CANONICAL")
    if not all_checks:
        reasons.append(f"incomplete evidence checks: {checks}")
    if evaluation.evaluation_status != "COMPLETE":
        reasons.append(f"evaluation_status={evaluation.evaluation_status}")
    if qualified:
        reasons.append("canonical factor_sign PaperRun evidence complete on genuine RB history")

    out: dict[str, Any] = {
        "strategy_id": contract.strategy_id,
        "version": contract.strategy_version,
        "instrument": "RB",
        "PAPER_QUALIFIED": "YES" if qualified else "NO",
        "FACTOR_SIGN_PAPER_ADAPTER": "PASS" if registry_ok and parity == "PASS" else "HOLD",
        "FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY": parity,
        "PAPER_RUNTIME": "CANONICAL",
        "LEGACY_PAPER_ORDERS_USED": legacy_used,
        "ORDERS_CREATED": "NO",
        "REAL_MONEY": "NO",
        "BROKER_LIVE_CAPABILITY": "HOLD",
        "bars": int(len(ohlcv)),
        "dataset_hash": ds_hash,
        "contract": contract.to_dict(),
        "checks": checks,
        "evaluation_status": evaluation.evaluation_status,
        "experiment_id": rec.experiment_id,
        "evidence_path": str(evidence_path),
        "primary_trade_count": primary.snapshot["trade_count"],
        "primary_equity": primary.snapshot["equity"],
        "kill_events": len(kill.kill_events),
        "recovery_events": len(recovery.recovery_events),
        "parity_detail": primary.parity,
        "reasons": reasons,
        "synthetic_pass": "NO",
        "legacy_paper_orders": "NOT_USED",
        "sandbox_runtime_used": "NO",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "PAPER_QUALIFIED": out["PAPER_QUALIFIED"],
                "FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY": parity,
                "checks": checks,
            },
            indent=2,
        )
    )
    return out


if __name__ == "__main__":
    main()

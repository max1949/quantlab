#!/usr/bin/env python3
"""Run Strategy Validation Batch 001 (Baseline Library).

Does NOT enable LIVE or Phase 7. Paper/parity default to INSUFFICIENT
until a dedicated Paper window is observed — no skip-level PASS.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.validation.baselines import baseline_library
from engine.validation.pipeline import validate_candidate


def main() -> int:
    out_dir = ROOT / "data" / "strategy_validation" / "batch_001"
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for cand in baseline_library():
        print(f"==> validating {cand.strategy_id} @ {cand.market} ...", flush=True)
        rep = validate_candidate(cand, write_graveyard=True)
        reports.append(rep.to_dict())
        (out_dir / f"{cand.strategy_id}.json").write_text(
            json.dumps(rep.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"    decision={rep.decision} overfit={rep.overfit_risk} gates={rep.gates}", flush=True)

    promoted = [r for r in reports if r["decision"] == "PROMOTE"]
    held = [r for r in reports if r["decision"] == "HOLD"]
    rejected = [r for r in reports if r["decision"] == "REJECT"]

    def _count_gate(name: str, want: str) -> int:
        return sum(1 for r in reports if (r.get("gates") or {}).get(name) == want)

    best = None
    best_score = -1e9
    for r in reports:
        ext = ((r.get("robustness") or {}).get("full_sample_extended") or {})
        sh = ext.get("sharpe")
        if sh is None:
            continue
        if float(sh) > best_score:
            best_score = float(sh)
            best = r

    summary = {
        "batch": "001",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "STRATEGIES_TESTED": len(reports),
        "PROMOTED": len(promoted),
        "HELD": len(held),
        "REJECTED": len(rejected),
        "OOS_PASS": _count_gate("oos", "PASS"),
        "WALK_FORWARD_PASS": _count_gate("walk_forward", "PASS"),
        "ROBUSTNESS_PASS": _count_gate("robustness", "PASS"),
        "COST_STRESS_PASS": _count_gate("cost_stress", "PASS"),
        "PAPER_PASS": _count_gate("paper", "PASS"),
        "BEST_STRATEGY": (best or {}).get("strategy_id"),
        "BEST_STRATEGY_VERSION": (best or {}).get("strategy_version"),
        "BEST_MARKET": (best or {}).get("market"),
        "BEST_TIMEFRAME": (best or {}).get("timeframe"),
        "best_extended": ((best or {}).get("robustness") or {}).get("full_sample_extended"),
        "LIVE_EXECUTION": "DENY",
        "PHASE_7": "DENY",
        "ENGINEERING_MODE": "MAINTENANCE_ONLY",
        "reports": reports,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Human report block
    ext = summary.get("best_extended") or {}
    lines = [
        "STRATEGIES_TESTED=" + str(summary["STRATEGIES_TESTED"]),
        "PROMOTED=" + str(summary["PROMOTED"]),
        "HELD=" + str(summary["HELD"]),
        "REJECTED=" + str(summary["REJECTED"]),
        "",
        "OOS_PASS=" + str(summary["OOS_PASS"]),
        "WALK_FORWARD_PASS=" + str(summary["WALK_FORWARD_PASS"]),
        "ROBUSTNESS_PASS=" + str(summary["ROBUSTNESS_PASS"]),
        "COST_STRESS_PASS=" + str(summary["COST_STRESS_PASS"]),
        "PAPER_PASS=" + str(summary["PAPER_PASS"]),
        "",
        "BEST_STRATEGY=" + str(summary["BEST_STRATEGY"]),
        "BEST_STRATEGY_VERSION=" + str(summary["BEST_STRATEGY_VERSION"]),
        "BEST_MARKET=" + str(summary["BEST_MARKET"]),
        "BEST_TIMEFRAME=" + str(summary["BEST_TIMEFRAME"]),
        "",
        "MAX_DRAWDOWN=" + str(ext.get("max_drawdown")),
        "SHARPE=" + str(ext.get("sharpe")),
        "SORTINO=" + str(ext.get("sortino")),
        "CALMAR=" + str(ext.get("calmar")),
        "PROFIT_FACTOR=" + str(ext.get("profit_factor")),
        "TRADE_COUNT=" + str(ext.get("trade_count")),
        "",
        "BACKTEST_PAPER_PARITY=INSUFFICIENT",
        "OVERFIT_RISK=" + str((best or {}).get("overfit_risk")),
        "",
        "LIVE_EXECUTION=DENY",
        "PHASE_7=DENY",
    ]
    report_txt = "\n".join(lines) + "\n"
    (out_dir / "REPORT.txt").write_text(report_txt, encoding="utf-8")
    print("\n==== BATCH 001 REPORT ====")
    print(report_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

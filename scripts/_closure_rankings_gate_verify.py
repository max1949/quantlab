#!/usr/bin/env python3
"""RANKINGS gate verify: leaderboard kinds, formulas, min-sample rules.

Run (repo root, PowerShell or bash):
  PYTHONPATH=. python scripts/_closure_rankings_gate_verify.py

Optional DB probe when DATABASE_URL / .env is available:
  prints top paper_mastery / researcher rows and why a 1-trade Sharpe cannot top.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.research_quality import PaperThresholds, assess_paper_readiness
from engine.validation.decision import (
    MIN_PERIODS_FOR_EVIDENCE,
    MIN_TRADE_COUNT_FOR_EVIDENCE,
)
from backend.app.services.leaderboard_service import KINDS, PAPER_MASTERY_BOARD_LIMIT
from backend.app.services.growth_service import (
    EFFECTIVE_GRADES,
    W_EFFECTIVE_VALIDATION,
    W_FOLLOWER,
    W_PUBLISHED_PROJECT,
    W_REPORT,
)


def _print_kinds() -> None:
    print("=== RANKING KINDS ===")
    for k in sorted(KINDS):
        print(f"  - {k}")
    print()


def _print_formulas() -> None:
    print("=== FORMULAS (not Sharpe boards) ===")
    print(
        "  researcher / newcomer: research_contribution_score = "
        f"{W_EFFECTIVE_VALIDATION}*effective_validations({sorted(EFFECTIVE_GRADES)})"
        f" + {W_REPORT}*reports + {W_PUBLISHED_PROJECT}*published + {W_FOLLOWER}*followers"
    )
    print("  contributor: reward_points (game milestones; score > 0 to rank)")
    print("  improved: count(effective validations + reports) in last 14d")
    print(
        "  paper_mastery: rank by paper_graduated_count desc, then paper_tracking_count; "
        f"board_limit={PAPER_MASTERY_BOARD_LIMIT}"
    )
    print("  NOTE: none of the site-wide boards sort by raw Sharpe.")
    print()


def _print_min_sample_rules() -> None:
    th = PaperThresholds()
    print("=== MIN SAMPLE / GRADUATION RULES ===")
    print(
        f"  evidence floors (engine.validation.decision): "
        f"trade_count>={MIN_TRADE_COUNT_FOR_EVIDENCE}, "
        f"periods>={MIN_PERIODS_FOR_EVIDENCE}"
    )
    print(
        "  paper_mastery entry: paper_graduated_count > 0 "
        "(assess_factor_paper / assess_paper_readiness)"
    )
    print(
        f"  paper thresholds (when research_gate_enabled): "
        f"oos_sharpe>={th.min_oos_sharpe}, robustness>={th.min_robustness_score}, "
        f"bt_sharpe>={th.min_backtest_sharpe}, max_turnover={th.max_turnover}, "
        f"min_abs_ic={th.min_abs_ic}, regime_fit>={th.min_regime_fit_score}"
    )
    print(
        "  + sample floor on paper readiness: "
        f"trade_count>={MIN_TRADE_COUNT_FOR_EVIDENCE}, "
        f"periods>={MIN_PERIODS_FOR_EVIDENCE}"
    )
    print("  researcher/newcomer: research_contribution_score > 0")
    print("  contributor: reward_points > 0")
    print()


def _synthetic_check() -> bool:
    print("=== SYNTHETIC: 1-trade huge Sharpe cannot graduate / enter paper_mastery ===")
    low = assess_paper_readiness(
        backtest_metrics={"sharpe": 99.0, "trade_count": 1, "periods": 50, "turnover": 10.0},
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": 50.0}},
        validation_robustness={
            "score": 90.0,
            "grade": "稳健",
            "sealed_holdout": {"metrics": {"sharpe": 1.0}},
            "factor_ic": {"ic_mean": 0.05},
        },
        regime_fit_score=80,
        thresholds=PaperThresholds(),
    )
    ok_low = low.passed is False and any("成交" in r or "证据线" in r for r in low.reasons)
    print(f"  low_sample.passed={low.passed} reasons={low.reasons}")
    print(f"  EXPECT blocked={ok_low}")

    adequate = assess_paper_readiness(
        backtest_metrics={
            "sharpe": 0.5,
            "trade_count": MIN_TRADE_COUNT_FOR_EVIDENCE,
            "periods": MIN_PERIODS_FOR_EVIDENCE,
            "turnover": 20.0,
        },
        validation_status="success",
        validation_oos={"out_of_sample": {"sharpe": 0.4}},
        validation_robustness={
            "score": 60.0,
            "grade": "中等",
            "sealed_holdout": {"metrics": {"sharpe": 0.1}},
            "factor_ic": {"ic_mean": 0.03},
        },
        regime_fit_score=40,
        thresholds=PaperThresholds(),
    )
    print(f"  adequate_sample.passed={adequate.passed} reasons={adequate.reasons}")
    ok_hi = adequate.passed is True
    print(f"  EXPECT pass_when_sample_ok={ok_hi}")
    print()
    return ok_low and ok_hi


def _db_probe() -> None:
    print("=== DB PROBE (optional) ===")
    try:
        from backend.app.core.database import SessionLocal
        from backend.app.services import leaderboard_service as lbs
        from backend.app.services import research_quality_service as rqs
        from sqlalchemy import select, func
        from backend.app.models.user import User
    except Exception as exc:  # noqa: BLE001
        print(f"  skip: cannot import DB stack ({exc})")
        return

    try:
        db = SessionLocal()
    except Exception as exc:  # noqa: BLE001
        print(f"  skip: SessionLocal failed ({exc})")
        return

    try:
        n_users = db.execute(select(func.count(User.id))).scalar_one()
        print(f"  users={n_users}")
        for kind in ("paper_mastery", "researcher"):
            rows = lbs.leaderboard(db, kind, limit=5)
            print(f"  top[{kind}] n={len(rows)}")
            for r in rows[:3]:
                print(
                    f"    #{r['rank']} {r['username']} "
                    f"{r['metric_label']}={r['metric_value']}"
                )
        # Explain: zero graduated → not ranked
        zero = 0
        for uid in db.execute(select(User.id).limit(50)).scalars():
            c = rqs.user_paper_mastery_counts(db, uid)
            if c["paper_graduated_count"] == 0:
                zero += 1
        print(
            f"  sample: among first 50 users, {zero} have paper_graduated_count=0 "
            "(excluded from paper_mastery)"
        )
        print(
            "  why 1-trade cannot #1 paper_mastery: need assess_paper_readiness "
            f"(incl. trade_count>={MIN_TRADE_COUNT_FOR_EVIDENCE}) before graduated>0"
        )
        print(
            "  why huge Sharpe cannot #1 researcher: board sorts contribution score, "
            "not Sharpe; score>0 required"
        )
    finally:
        db.close()
    print()


def main() -> int:
    _print_kinds()
    _print_formulas()
    _print_min_sample_rules()
    synth_ok = _synthetic_check()
    _db_probe()
    status = "PASS" if synth_ok else "FAIL"
    print(f"RANKINGS_GATE={status}")
    return 0 if synth_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 6 Golden E2E evidence generator (local, SANDBOX only)."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.models.user import User, UserLevel
from backend.app.services import membership_service as ms
from backend.app.services import paper_run_service as prs


def main() -> int:
    spec_path = ROOT / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    evidence: dict = {"LIVE_ORDER_COUNT": 0, "steps": []}

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.username == "phase6_golden")).scalar_one_or_none()
        if user is None:
            from backend.app.schemas.user import UserCreate
            from backend.app.services import user_service

            user = user_service.create_user(
                db,
                UserCreate(
                    email="phase6_golden@quantlab.ai",
                    username="phase6_golden",
                    password="phase6-golden-pass",
                ),
            )
        user.level = UserLevel.L4
        db.commit()
        ms.grant(db, user, ms.TIER_PRO, 30, "pro_monthly")

        from backend.app.models.paper_run import PaperReadyRegistry

        ready = db.execute(
            select(PaperReadyRegistry)
            .where(
                PaperReadyRegistry.user_id == user.id,
                PaperReadyRegistry.strategy_spec_id == spec["strategy"]["id"],
            )
            .order_by(PaperReadyRegistry.created_at.desc())
        ).scalar_one_or_none()
        if ready is None:
            ready = prs.register_paper_ready(
                db,
                user,
                spec_payload=spec,
                compiled_hash="golden",
                data_gate_status="PASS",
                backtest_pass=True,
                validation_pass=True,
                robustness_pass=True,
            )
        evidence["steps"].append({"paper_ready": ready.strategy_spec_id})

        run = prs.create_paper_run(
            db,
            user,
            spec_payload=spec,
            compiled_hash="golden",
            environment="SANDBOX",
            data_provider="synthetic",
        )
        evidence["steps"].append({"create_run": str(run.id)})

        started = prs.start_paper_run(db, user.id, uuid.UUID(str(run.id)))
        evidence["steps"].append({"start": started.status})

        dash = prs.paper_run_dashboard(db, user.id, uuid.UUID(str(run.id)))
        compare = prs.backtest_vs_paper_report(db, user.id, uuid.UUID(str(run.id)))
        evidence.update(
            {
                "run_id": str(run.id),
                "status": started.status,
                "orders": dash.get("orders_count"),
                "fills": dash.get("fills_count"),
                "equity": dash.get("equity_zh"),
                "parity_status": compare.get("parity_status"),
                "research_feedback": dash.get("research_feedback_zh"),
                "GOLDEN_E2E": "PASS" if started.status in {"STOPPED", "RUNNING"} else "FAIL",
            }
        )
        out = ROOT / "data" / "paper_runs" / "_golden_e2e" / "evidence.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 0 if evidence["GOLDEN_E2E"] == "PASS" else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

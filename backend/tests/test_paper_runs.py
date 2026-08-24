"""Phase 6 PaperRun API tests."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

BASE = "/api/v1/paper-sandbox"
USER = {"email": "paper6@quantlab.ai", "username": "paper6user", "password": "s3cret-pass"}


def _auth(client) -> dict:
    client.post("/api/v1/auth/register", json=USER)
    tok = client.post(
        "/api/v1/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _pro_headers(client, db_session):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from sqlalchemy import select

    h = _auth(client)
    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")
    return h


def _btc_spec() -> dict:
    path = Path(__file__).resolve().parents[2] / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_live_environment_denied(client, db_session):
    h = _pro_headers(client, db_session)
    spec = _btc_spec()
    ready = client.post(f"{BASE}/paper-ready", headers=h, json={"spec": spec})
    assert ready.status_code == 200, ready.text

    created = client.post(
        f"{BASE}/runs",
        headers=h,
        json={"spec": spec, "environment": "LIVE"},
    )
    assert created.status_code in {403, 422}


def test_paper_run_e2e_synthetic(client, db_session):
    h = _pro_headers(client, db_session)
    spec = _btc_spec()

    ready = client.post(
        f"{BASE}/paper-ready",
        headers=h,
        json={
            "spec": spec,
            "compiled_hash": "abc123",
            "data_gate_status": "PASS",
            "backtest_pass": True,
            "validation_pass": True,
            "robustness_pass": True,
        },
    )
    assert ready.status_code == 200, ready.text

    run = client.post(
        f"{BASE}/runs",
        headers=h,
        json={"spec": spec, "environment": "SANDBOX", "data_provider": "synthetic"},
    )
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]
    assert run.json()["simulated_balance"] is True

    started = client.post(f"{BASE}/runs/{run_id}/start", headers=h)
    assert started.status_code == 200, started.text
    assert started.json()["status"] in {"STOPPED", "RUNNING", "FAILED"}

    dash = client.get(f"{BASE}/runs/{run_id}/dashboard", headers=h)
    assert dash.status_code == 200, dash.text
    body = dash.json()
    assert body["title_zh"] == "模拟交易"
    assert "不涉及真实资金" in body["disclaimer_zh"]

    analyst = client.post(
        f"{BASE}/runs/{run_id}/analyst",
        headers=h,
        json={"question": "为什么今天亏损？"},
    )
    assert analyst.status_code == 200
    assert "AI 仅解释" in analyst.json()["answer_zh"]


def test_kill_switch(client, db_session):
    h = _pro_headers(client, db_session)
    spec = _btc_spec()
    client.post(f"{BASE}/paper-ready", headers=h, json={"spec": spec})
    run_id = client.post(
        f"{BASE}/runs",
        headers=h,
        json={"spec": spec, "environment": "SANDBOX", "data_provider": "synthetic"},
    ).json()["id"]
    killed = client.post(f"{BASE}/runs/{run_id}/kill", headers=h)
    assert killed.status_code == 200
    assert killed.json()["status"] == "KILLED"

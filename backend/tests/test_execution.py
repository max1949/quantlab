"""制度×策略适配与模拟执行测试。"""

from __future__ import annotations

import pytest

from backend.app.services import membership_service as ms

BASE = "/api/v1"

USER = {"email": "exec1@quantlab.ai", "username": "execuser", "password": "s3cret-pass"}


def _auth(client, user=USER) -> dict:
    client.post(f"{BASE}/auth/register", json=user)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": user["username"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _pro_headers(client, db_session):
    h = _auth(client)
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")
    return h


def test_regime_with_factor_fit(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom", "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]

    resp = client.get(
        f"{BASE}/datasets/regime",
        headers=h,
        params={"symbol": "RB", "factor_id": fid},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["regime"] in ("low", "mid", "high")
    assert body.get("strategy_style") == "trend"
    assert "fit_score" in body
    assert body["fit_verdict"] in ("适合", "一般", "谨慎")


def test_backtest_includes_strategy_fit(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "rev", "template_type": "mean_reversion", "params": {"window": 10}},
    ).json()["id"]
    bt = client.post(
        f"{BASE}/backtests",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "timeframe": "1d"},
    ).json()
    detail = client.get(f"{BASE}/backtests/{bt['id']}", headers=h).json()
    regime = detail.get("market_regime") or {}
    assert regime.get("strategy_style") == "mean_reversion"
    assert "fit_score" in regime


def test_paper_order_requires_pro(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _auth(client)
    seed_sample_market_data(db_session)
    resp = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "buy", "notional_cny": 10000},
    )
    assert resp.status_code == 403


def test_paper_order_submit_and_list(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "execmom", "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]

    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={
            "symbol": "RB",
            "side": "buy",
            "notional_cny": 50000,
            "factor_id": fid,
            "signal_value": 0.82,
            "note": "test order",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "filled"
    assert body["channel"] == "paper"
    assert body["regime"] in ("low", "mid", "high", None)
    assert body["regime_fit_score"] is not None

    listed = client.get(f"{BASE}/execution/paper/orders", headers=h)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_execution_config(client, db_session):
    h = _pro_headers(client, db_session)
    resp = client.get(f"{BASE}/execution/config", headers=h)
    assert resp.status_code == 200
    body = resp.json()
    assert "channels" in body
    assert body["max_notional_cny"] > 0


def test_risk_preflight_blocks_vnpy_low_fit():
    from unittest.mock import MagicMock

    from backend.app.services.execution_risk import RiskBlockedError, preflight

    settings = MagicMock()
    settings.execution_kill_switch = False
    settings.execution_max_notional_cny = 5_000_000
    settings.execution_min_regime_fit_vnpy = 80

    from backend.app.services import execution_risk as er

    orig = er.get_settings
    er.get_settings = lambda: settings
    try:
        with pytest.raises(RiskBlockedError):
            preflight(notional_cny=10000, channel="vnpy", regime_fit_score=30)
        ok = preflight(
            notional_cny=10000, channel="vnpy", regime_fit_score=30, acknowledge_risk=True
        )
        assert ok["verdict"] == "passed"
    finally:
        er.get_settings = orig


def test_vnpy_channel_stub_order(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)

    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={
            "symbol": "RB",
            "side": "sell",
            "notional_cny": 20000,
            "channel": "vnpy",
            "acknowledge_risk": True,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["channel"] == "vnpy"
    assert body["status"] == "routed"
    assert body["external_ref"] and body["external_ref"].startswith("VNPY-")


def test_route_paper_to_vnpy(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)
    order = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "buy", "notional_cny": 15000, "channel": "paper"},
    ).json()

    routed = client.post(f"{BASE}/execution/paper/orders/{order['id']}/route-vnpy", headers=h)
    assert routed.status_code == 200, routed.text
    assert routed.json()["channel"] == "vnpy"
    assert routed.json()["external_ref"]

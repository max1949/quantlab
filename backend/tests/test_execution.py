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


def test_vnpy_channel_new_create_rejected(client, db_session):
    """Phase 5: NEW vn.py creates are denied; historical rows remain readable."""
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
    assert created.status_code == 422, created.text
    assert "VNPY_LEGACY" in created.text or "停止新增" in created.text


def test_route_paper_to_vnpy_gone(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)
    order = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "buy", "notional_cny": 15000, "channel": "paper"},
    ).json()

    routed = client.post(f"{BASE}/execution/paper/orders/{order['id']}/route-vnpy", headers=h)
    assert routed.status_code == 410, routed.text


def test_qmt_channel_new_create_denied(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)

    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={
            "symbol": "RB",
            "side": "buy",
            "notional_cny": 30000,
            "channel": "qmt",
            "acknowledge_risk": True,
        },
    )
    assert created.status_code == 422, created.text
    assert "QMT_LEGACY" in created.text


def _legacy_qmt_order(db_session, user_id):
    import uuid
    from backend.app.models.execution import PaperOrder

    order = PaperOrder(
        id=uuid.uuid4(),
        user_id=user_id,
        symbol="RB",
        side="buy",
        notional_cny=12000,
        status="routed",
        channel="qmt",
        external_ref="QMT-LEGACY-TEST",
        risk_verdict="passed",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order

def test_gateway_webhook_updates_order(client, db_session):
    import hashlib
    import hmac
    import json

    from backend.app.core.config import get_settings

    h = _pro_headers(client, db_session)
    from backend.app.models.user import User
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    order = _legacy_qmt_order(db_session, user.id)
    ref = order.external_ref
    assert ref

    settings = get_settings()
    prev = settings.execution_webhook_secret
    secret = "whsec-test-56"
    settings.execution_webhook_secret = secret
    try:
        payload = {"external_ref": ref, "status": "filled"}
        body = json.dumps(payload, separators=(",", ":")).encode()
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        resp = client.post(
            f"{BASE}/execution/webhook/gateway",
            content=body,
            headers={"Content-Type": "application/json", "X-Gateway-Signature": sig},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "filled"

        detail = client.get(f"{BASE}/execution/paper/orders/{order.id}", headers=h).json()
        assert detail["status"] == "filled"
        assert detail["gateway_status"] == "filled"
        assert detail["filled_at"] is not None

        body2 = json.dumps({"external_ref": ref, "status": "rejected"}, separators=(",", ":")).encode()
        sig2 = hmac.new(secret.encode(), body2, hashlib.sha256).hexdigest()
        bad = client.post(
            f"{BASE}/execution/webhook/gateway",
            content=body2,
            headers={"Content-Type": "application/json", "X-Gateway-Signature": sig2},
        )
        assert bad.status_code == 200
        assert bad.json()["status"] == "rejected"
    finally:
        settings.execution_webhook_secret = prev


def test_gateway_webhook_rejects_bad_signature(client, db_session):
    from backend.app.core.config import get_settings

    settings = get_settings()
    prev = settings.execution_webhook_secret
    settings.execution_webhook_secret = "secret"
    try:
        resp = client.post(
            f"{BASE}/execution/webhook/gateway",
            json={"external_ref": "NOPE", "status": "filled"},
            headers={"X-Gateway-Signature": "invalid"},
        )
        assert resp.status_code == 400
    finally:
        settings.execution_webhook_secret = prev


def test_order_events_timeline(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)
    order = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "buy", "notional_cny": 8000, "channel": "paper"},
    ).json()

    events = client.get(f"{BASE}/execution/paper/orders/{order['id']}/events", headers=h)
    assert events.status_code == 200, events.text
    body = events.json()
    assert len(body) >= 1
    assert body[0]["event_type"] == "submitted"
    assert body[0]["to_status"] == "filled"


def test_route_paper_to_qmt_retired(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data

    h = _pro_headers(client, db_session)
    seed_sample_market_data(db_session)
    order = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "sell", "notional_cny": 18000, "channel": "paper"},
    ).json()

    routed = client.post(f"{BASE}/execution/paper/orders/{order['id']}/route-qmt", headers=h)
    assert routed.status_code == 410, routed.text
    assert "QMT_LEGACY" in routed.text

def test_refresh_gateway_order_poll(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.execution_service.fetch_gateway_order_status",
        lambda **_: "filled",
    )

    h = _pro_headers(client, db_session)
    from backend.app.models.user import User
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    order = _legacy_qmt_order(db_session, user.id)

    refreshed = client.post(f"{BASE}/execution/paper/orders/{order.id}/refresh", headers=h)
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["status"] == "filled"
    assert refreshed.json()["gateway_status"] == "filled"

    events = client.get(f"{BASE}/execution/paper/orders/{order.id}/events", headers=h).json()
    assert any(e["event_type"] == "gateway_poll" for e in events)


def test_execution_gateway_health_endpoint(client, db_session):
    h = _pro_headers(client, db_session)
    resp = client.get(f"{BASE}/execution/gateway-health", headers=h)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["gateways"]) == 2
    assert {g["channel"] for g in body["gateways"]} == {"vnpy", "qmt"}
    vn = next(g for g in body["gateways"] if g["channel"] == "vnpy")
    assert vn.get("mode") == "retired" or vn.get("deprecated") is True or vn.get("ok") is False


def test_sync_all_pending_gateway_orders(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.execution_service.fetch_gateway_order_status",
        lambda **_: "filled",
    )
    from backend.app.services import execution_service as exs
    from backend.app.models.user import User
    from sqlalchemy import select

    h = _pro_headers(client, db_session)
    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    _legacy_qmt_order(db_session, user.id)
    result = exs.sync_all_pending_gateway_orders(db_session)
    assert result["checked"] >= 1
    assert result["updated"] >= 1
    assert result.get("skipped") is False


def test_sync_gateway_orders_task(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.execution_service.fetch_gateway_order_status",
        lambda **_: "filled",
    )
    from backend.app.services import execution_service as exs
    from backend.app.models.user import User
    from sqlalchemy import select

    h = _pro_headers(client, db_session)
    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    _legacy_qmt_order(db_session, user.id)
    out = exs.sync_all_pending_gateway_orders(db_session)
    assert out["checked"] >= 1


def test_refresh_legacy_qmt_retired(client, db_session):
    h = _pro_headers(client, db_session)
    from backend.app.models.user import User
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    order = _legacy_qmt_order(db_session, user.id)

    resp = client.post(f"{BASE}/execution/paper/orders/{order.id}/refresh", headers=h)
    assert resp.status_code == 422
    assert "QMT_LEGACY" in resp.json()["detail"]

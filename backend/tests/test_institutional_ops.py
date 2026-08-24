"""机构平台基础: 就绪探针、运营指标、审计、制度识别、因子资产库。"""

from __future__ import annotations

from backend.app.core.config import get_settings
from backend.app.services import audit_service, ops_metrics_service
from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"

USER = {"email": "ops@quantlab.ai", "username": "opstester", "password": "s3cret-pass"}


def _auth(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _admin_headers() -> dict:
    key = get_settings().admin_api_key or "test-admin-key"
    get_settings().admin_api_key = key
    return {"X-Admin-Key": key}


def test_health_ready_ok(client, db_session):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["database"]["ok"] is True


def test_admin_ops_metrics_requires_key(client, db_session):
    resp = client.get(f"{BASE}/admin/ops/metrics")
    assert resp.status_code == 403


def test_admin_ops_metrics_with_key(client, db_session):
    client.post(f"{BASE}/auth/register", json=USER)
    metrics = ops_metrics_service.compute_pmf_metrics(db_session)
    assert "registered_users" in metrics
    assert "funnel" in metrics
    assert "institutional" in metrics

    resp = client.get(f"{BASE}/admin/ops/metrics", headers=_admin_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered_users"] >= 1


def test_admin_ops_audit_empty(client, db_session):
    resp = client.get(f"{BASE}/admin/ops/audit", headers=_admin_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_audit_service_log(client, db_session):
    from backend.app.models.user import User

    u = User(email="a@x.com", username="audittest", hashed_password="x")
    db_session.add(u)
    db_session.commit()
    audit_service.log(
        db_session,
        actor_id=u.id,
        action="test.action",
        resource_type="test",
        resource_id="1",
        detail={"k": "v"},
    )
    rows = audit_service.list_recent(db_session, limit=5)
    assert len(rows) == 1
    assert rows[0].action == "test.action"


def test_dataset_regime(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    resp = client.get(f"{BASE}/datasets/regime", headers=h, params={"symbol": "RB"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["symbol"] == "RB"
    assert body["regime"] in ("low", "mid", "high")


def test_factor_catalog(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "cat", "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]
    client.post(
        f"{BASE}/backtests",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "fee_rate": 0.0005, "slippage_bps": 1.0},
    )
    resp = client.get(f"{BASE}/factors/catalog", headers=h, params={"symbol": "RB"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["factors"]) >= 1
    assert body["factors"][0]["factor_id"] == fid


def test_admin_execution_health_and_sync(client, db_session, monkeypatch, legacy_qmt_order):
    monkeypatch.setattr(
        "backend.app.services.execution_service.fetch_gateway_order_status",
        lambda **_: "filled",
    )
    from backend.app.models.user import UserLevel
    from backend.app.services import membership_service as ms
    from sqlalchemy import select
    from backend.app.models.user import User

    h = _auth(client)
    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    legacy_qmt_order(user.id, notional_cny=13000)

    health = client.get(f"{BASE}/admin/ops/execution/health", headers=_admin_headers())
    assert health.status_code == 200, health.text
    assert len(health.json()["gateways"]) == 2

    sync = client.post(f"{BASE}/admin/ops/execution/sync", headers=_admin_headers())
    assert sync.status_code == 200, sync.text
    assert sync.json()["checked"] >= 1

    metrics = client.get(f"{BASE}/admin/ops/metrics", headers=_admin_headers()).json()
    assert "gateway_health" in metrics["institutional"]
    assert "routed_gateway_orders" in metrics["institutional"]

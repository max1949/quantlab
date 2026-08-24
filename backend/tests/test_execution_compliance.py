"""执行合规与 SLA 告警测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.app.core.config import get_settings
from backend.app.services import membership_service as ms

BASE = "/api/v1"

USER = {"email": "sla@quantlab.ai", "username": "slauser", "password": "s3cret-pass"}


def _admin_headers() -> dict:
    key = get_settings().admin_api_key or "test-admin-key"
    get_settings().admin_api_key = key
    return {"X-Admin-Key": key}


def _pro_headers(client, db_session):
    client.post(f"{BASE}/auth/register", json=USER)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")
    return h


def test_admin_execution_compliance_report(client, db_session):
    resp = client.get(f"{BASE}/admin/ops/execution/compliance", headers=_admin_headers())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scope"] == "global"
    assert "order_summary" in body
    assert "sla_alerts" in body
    assert body["sla_stale_minutes"] >= 1


def test_stale_routed_order_triggers_sla_alert(client, db_session, legacy_qmt_order):
    import uuid

    from backend.app.models.execution import PaperOrder

    settings = get_settings()
    prev = settings.execution_sla_stale_minutes
    settings.execution_sla_stale_minutes = 30

    h = _pro_headers(client, db_session)
    from backend.app.models.user import User
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == USER["username"])).scalar_one()
    order = legacy_qmt_order(user.id, notional_cny=10000)

    row = db_session.get(PaperOrder, order.id)
    row.routed_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.add(row)
    db_session.commit()

    try:
        resp = client.get(f"{BASE}/admin/ops/execution/compliance", headers=_admin_headers())
        assert resp.status_code == 200
        alerts = resp.json()["sla_alerts"]
        assert any(a["code"] == "stale_routed_order" for a in alerts)
        assert len(resp.json()["stale_orders"]) >= 1
    finally:
        settings.execution_sla_stale_minutes = prev


def test_org_execution_compliance(client, db_session):
    owner = {"email": "orgsla@x.com", "username": "orgslaowner", "password": "s3cret-pass"}
    client.post(f"{BASE}/auth/register", json=owner)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": owner["username"], "password": owner["password"]},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    org_id = client.post(f"{BASE}/orgs", headers=h, json={"name": "SLA Desk"}).json()["id"]
    resp = client.get(f"{BASE}/orgs/{org_id}/execution/compliance", headers=h)
    assert resp.status_code == 200, resp.text
    assert resp.json()["scope"] == "org"
    assert str(resp.json()["org_id"]) == org_id

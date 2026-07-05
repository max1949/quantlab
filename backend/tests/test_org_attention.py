"""机构团队研究提醒汇总测试。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from backend.app.core.config import get_settings
from backend.app.services import execution_alert_service as eas
from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"

OWNER = {"email": "attn1@quantlab.ai", "username": "attnowner", "password": "s3cret-pass"}
MEMBER = {"email": "attn2@quantlab.ai", "username": "attnmember", "password": "s3cret-pass"}


def _auth(client, user=OWNER) -> dict:
    client.post(f"{BASE}/auth/register", json=user)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": user["username"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_org_team_attention_rollup_empty(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    seed_sample_market_data(db_session)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Alert Desk"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    resp = client.get(f"{BASE}/orgs/{org_id}/research/attention-alerts", headers=h_owner)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["member_count"] == 2
    assert body["total_alerts"] == 0
    assert body["items"] == []
    assert body["summary"]

    denied = client.get(f"{BASE}/orgs/{org_id}/research/attention-alerts", headers=h_member)
    assert denied.status_code == 403


def test_org_research_attention_webhook_dispatch(client, db_session):
    settings = get_settings()
    prev_enabled = settings.execution_sla_alert_enabled
    settings.execution_sla_alert_enabled = True

    owner = {"email": "reswh@x.com", "username": "reswhowner", "password": "s3cret-pass"}
    client.post(f"{BASE}/auth/register", json=owner)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": owner["username"], "password": owner["password"]},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    org_id = client.post(f"{BASE}/orgs", headers=h, json={"name": "Research WH"}).json()["id"]

    client.put(
        f"{BASE}/orgs/{org_id}/execution/alert-webhook",
        headers=h,
        json={
            "webhook_url": "https://hooks.example.com/org-research",
            "webhook_secret": "research-secret",
        },
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("backend.app.services.execution_alert_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        fake_item = {
            "username": "alice",
            "alert_key": "regime_shift:abc",
            "kind": "regime_shift",
            "title": "Regime shift",
            "message": "test",
            "severity": "watch",
        }
        with patch(
            "backend.app.services.org_attention_service.collect_team_attention"
        ) as mock_rollup:
            mock_rollup.return_value = {
                "member_count": 1,
                "members_with_alerts": 1,
                "total_alerts": 1,
                "summary": "1 alert",
                "items": [fake_item],
            }
            resp = client.post(
                f"{BASE}/orgs/{org_id}/research/attention-alerts/dispatch",
                headers=h,
                params={"force": True},
            )

    try:
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["sent"] == 1
        assert body["scope"] == "org_research"
        call_kwargs = mock_client.post.call_args.kwargs
        body_bytes = call_kwargs["content"]
        sig = call_kwargs["headers"][eas.SIGNATURE_HEADER]
        assert eas.verify_webhook_signature(body_bytes, sig, "research-secret")
        payload = json.loads(body_bytes.decode())
        assert payload["event"] == "research_attention_rollup"
        assert payload["org_id"] == org_id
    finally:
        settings.execution_sla_alert_enabled = prev_enabled


def test_org_team_attention_rollup_with_member_project(client, db_session):
    h_owner = _auth(client, OWNER)
    h_member = _auth(client, MEMBER)
    seed_sample_market_data(db_session)

    org_id = client.post(f"{BASE}/orgs", headers=h_owner, json={"name": "Coach Org"}).json()["id"]
    client.post(
        f"{BASE}/orgs/{org_id}/members",
        headers=h_owner,
        json={"username": MEMBER["username"], "role": "member"},
    )

    proj = client.post(
        f"{BASE}/projects",
        headers=h_member,
        json={"title": "member-p", "symbol": "RB"},
    ).json()
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h_member,
        json={
            "name": "m-mom",
            "template_type": "momentum",
            "params": {"window": 20},
            "project_id": proj["id"],
        },
    ).json()["id"]
    client.post(f"{BASE}/backtests", headers=h_member, json={"factor_id": fid, "symbol": "RB"})
    client.post(
        f"{BASE}/validations",
        headers=h_member,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    )

    resp = client.get(f"{BASE}/orgs/{org_id}/research/attention-alerts", headers=h_owner)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["member_count"] >= 1
    if body["total_alerts"] > 0:
        item = body["items"][0]
        assert item["username"] == MEMBER["username"]
        assert item["kind"] in ("regime_shift", "weak_regime_fit", "paper_decay")
        assert item["cta_path"]

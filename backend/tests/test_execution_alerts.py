"""执行 SLA 告警 Webhook 推送测试。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from backend.app.core.config import get_settings
from backend.app.services import execution_alert_service as eas

BASE = "/api/v1"


def _admin_headers() -> dict:
    key = get_settings().admin_api_key or "test-admin-key"
    get_settings().admin_api_key = key
    return {"X-Admin-Key": key}


def test_dispatch_skipped_when_webhook_not_configured(client, db_session):
    settings = get_settings()
    prev_url = settings.execution_sla_webhook_url
    settings.execution_sla_webhook_url = ""
    try:
        resp = client.post(f"{BASE}/admin/ops/execution/alerts/dispatch", headers=_admin_headers())
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["skipped"] is True
        assert body["reason"] == "webhook_not_configured"
    finally:
        settings.execution_sla_webhook_url = prev_url


def test_dispatch_sends_webhook_on_kill_switch(client, db_session):
    settings = get_settings()
    prev_url = settings.execution_sla_webhook_url
    prev_secret = settings.execution_sla_webhook_secret
    prev_kill = settings.execution_kill_switch
    settings.execution_sla_webhook_url = "https://hooks.example.com/sla"
    settings.execution_sla_webhook_secret = "test-sla-secret"
    settings.execution_kill_switch = True

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("backend.app.services.execution_alert_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        with patch("backend.app.services.execution_alert_service.filter_new_alerts") as mock_filter:
            mock_filter.return_value = [
                {
                    "code": "kill_switch_on",
                    "severity": "critical",
                    "message": "执行总闸已关闭",
                }
            ]
            resp = client.post(
                f"{BASE}/admin/ops/execution/alerts/dispatch",
                headers=_admin_headers(),
                params={"force": True},
            )

    try:
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["sent"] == 1
        assert body["skipped"] is False
        assert body.get("signed") is True
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        body_bytes = call_kwargs["content"]
        sig = call_kwargs["headers"][eas.SIGNATURE_HEADER]
        assert eas.verify_webhook_signature(body_bytes, sig, "test-sla-secret")
        payload = json.loads(body_bytes.decode())
        assert payload["event"] == "execution_sla_alert"
        assert payload["alerts"][0]["code"] == "kill_switch_on"
    finally:
        settings.execution_sla_webhook_url = prev_url
        settings.execution_sla_webhook_secret = prev_secret
        settings.execution_kill_switch = prev_kill


def test_alert_fingerprint_stable():
    a = {"code": "gateway_down", "channel": "qmt", "order_id": None}
    b = {"code": "gateway_down", "channel": "qmt"}
    assert eas.alert_fingerprint(a) == eas.alert_fingerprint(b)


def test_webhook_signature_roundtrip():
    payload = {"event": "execution_sla_alert", "alert_count": 1}
    body = eas.serialize_webhook_payload(payload)
    sig = eas.sign_webhook_body(body, "secret-key")
    assert eas.verify_webhook_signature(body, sig, "secret-key")
    assert not eas.verify_webhook_signature(body, "bad", "secret-key")


def test_org_alert_webhook_config_and_dispatch(client, db_session):
    settings = get_settings()
    prev_kill = settings.execution_kill_switch
    settings.execution_kill_switch = True

    owner = {"email": "orgwh@x.com", "username": "orgwhowner", "password": "s3cret-pass"}
    client.post(f"{BASE}/auth/register", json=owner)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": owner["username"], "password": owner["password"]},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    org_id = client.post(f"{BASE}/orgs", headers=h, json={"name": "Webhook Desk"}).json()["id"]

    get_empty = client.get(f"{BASE}/orgs/{org_id}/execution/alert-webhook", headers=h)
    assert get_empty.status_code == 200
    assert get_empty.json()["webhook_url"] == ""

    put = client.put(
        f"{BASE}/orgs/{org_id}/execution/alert-webhook",
        headers=h,
        json={"webhook_url": "https://hooks.example.com/org-sla"},
    )
    assert put.status_code == 200, put.text

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("backend.app.services.execution_alert_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        with patch("backend.app.services.execution_alert_service.filter_new_alerts") as mock_filter:
            mock_filter.return_value = [
                {"code": "kill_switch_on", "severity": "critical", "message": "kill switch"}
            ]
            resp = client.post(
                f"{BASE}/orgs/{org_id}/execution/alerts/dispatch",
                headers=h,
                params={"force": True},
            )

    try:
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["sent"] == 1
        assert body["scope"] == "org"
        body_bytes = mock_client.post.call_args.kwargs["content"]
        payload = json.loads(body_bytes.decode())
        assert payload["scope"] == "org"
        assert payload["org_id"] == org_id
    finally:
        settings.execution_kill_switch = prev_kill

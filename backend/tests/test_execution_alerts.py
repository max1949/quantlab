"""执行 SLA 告警 Webhook 推送测试。"""

from __future__ import annotations

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
    prev_kill = settings.execution_kill_switch
    settings.execution_sla_webhook_url = "https://hooks.example.com/sla"
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
        mock_client.post.assert_called_once()
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["event"] == "execution_sla_alert"
        assert payload["alerts"][0]["code"] == "kill_switch_on"
    finally:
        settings.execution_sla_webhook_url = prev_url
        settings.execution_kill_switch = prev_kill


def test_alert_fingerprint_stable():
    a = {"code": "gateway_down", "channel": "qmt", "order_id": None}
    b = {"code": "gateway_down", "channel": "qmt"}
    assert eas.alert_fingerprint(a) == eas.alert_fingerprint(b)

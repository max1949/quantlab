"""vn.py / QMT 执行适配器测试。"""

import hashlib
import hmac
import uuid

from engine.execution_adapter import route_qmt_order, route_vnpy_order, verify_gateway_webhook


def test_fetch_gateway_order_status_mocked(monkeypatch):
    from engine import execution_adapter as ea

    class _Settings:
        qmt_gateway_url = "http://qmt-gw"
        qmt_gateway_token = "tok"
        vnpy_gateway_url = ""
        vnpy_gateway_token = ""

    class _Resp:
        status_code = 200
        content = b'{"status":"filled"}'

        def json(self):
            return {"status": "filled"}

    class _Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, headers=None):
            assert "/orders/QMT-ABC" in url
            return _Resp()

    monkeypatch.setattr(ea, "get_settings", lambda: _Settings())
    monkeypatch.setattr(ea.httpx, "Client", _Client)

    status = ea.fetch_gateway_order_status(channel=ea.CHANNEL_QMT, external_ref="QMT-ABC")
    assert status == "filled"


def test_probe_gateway_health_stub():
    from engine.execution_adapter import CHANNEL_QMT, CHANNEL_VNPY, probe_gateway_health

    vn = probe_gateway_health(CHANNEL_VNPY)
    assert vn["configured"] is False
    assert vn["mode"] in {"stub", "retired"}
    qmt = probe_gateway_health(CHANNEL_QMT)
    assert qmt["configured"] is False


def test_vnpy_new_route_retired():
    """LEGACY_COMPAT: new vn.py routes must raise VnpyChannelRetired."""
    import pytest
    from engine.execution_adapter import VnpyChannelRetired

    with pytest.raises(VnpyChannelRetired):
        route_vnpy_order(
            order_id=uuid.uuid4(),
            symbol="RB",
            side="buy",
            notional_cny=10000,
        )


def test_probe_gateway_health_ok_mocked(monkeypatch):
    from engine import execution_adapter as ea

    class _Settings:
        qmt_gateway_url = "http://qmt-gw"
        qmt_gateway_token = ""
        vnpy_gateway_url = ""
        vnpy_gateway_token = ""

    class _Resp:
        status_code = 200
        content = b"ok"

    class _Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, headers=None):
            return _Resp()

    monkeypatch.setattr(ea, "get_settings", lambda: _Settings())
    monkeypatch.setattr(ea.httpx, "Client", _Client)

    out = ea.probe_gateway_health(ea.CHANNEL_QMT)
    assert out["configured"] is True
    assert out["ok"] is True


def test_qmt_stub_without_gateway():
    out = route_qmt_order(
        order_id=uuid.uuid4(),
        symbol="AU",
        side="sell",
        notional_cny=25000,
    )
    assert out["mode"] == "stub"
    assert out["external_ref"].startswith("QMT-STUB-")


def test_verify_gateway_webhook():
    secret = "test-webhook-secret"
    payload = b'{"external_ref":"QMT-STUB-ABC","status":"filled"}'
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_gateway_webhook(payload, sig, secret) is True
    assert verify_gateway_webhook(payload, "bad", secret) is False
    assert verify_gateway_webhook(payload, sig, "") is False

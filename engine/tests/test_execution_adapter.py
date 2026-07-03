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


def test_fetch_gateway_unconfigured_raises():
    import pytest

    from engine.execution_adapter import AdapterError, CHANNEL_QMT, fetch_gateway_order_status

    with pytest.raises(AdapterError, match="网关未配置"):
        fetch_gateway_order_status(channel=CHANNEL_QMT, external_ref="X")


def test_vnpy_stub_without_gateway():
    out = route_vnpy_order(
        order_id=uuid.uuid4(),
        symbol="RB",
        side="buy",
        notional_cny=10000,
    )
    assert out["mode"] == "stub"
    assert out["external_ref"].startswith("VNPY-STUB-")


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

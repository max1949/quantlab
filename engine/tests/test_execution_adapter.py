"""vn.py / QMT 执行适配器测试。"""

import hashlib
import hmac
import uuid

from engine.execution_adapter import route_qmt_order, route_vnpy_order, verify_gateway_webhook


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

"""vn.py / QMT 执行适配器测试。"""

import hashlib
import hmac
import uuid

import pytest

from engine.execution_adapter import (
    QmtChannelRetired,
    VnpyChannelRetired,
    route_qmt_order,
    route_vnpy_order,
    verify_gateway_webhook,
)


def test_fetch_gateway_order_status_qmt_retired():
    from engine import execution_adapter as ea

    with pytest.raises(QmtChannelRetired):
        ea.fetch_gateway_order_status(channel=ea.CHANNEL_QMT, external_ref="QMT-ABC")


def test_probe_gateway_health_stub():
    from engine.execution_adapter import CHANNEL_QMT, CHANNEL_VNPY, gateway_health_summary, probe_gateway_health

    vn = probe_gateway_health(CHANNEL_VNPY)
    assert vn["configured"] is False
    assert vn["mode"] in {"stub", "retired"}
    qmt = probe_gateway_health(CHANNEL_QMT)
    assert qmt["configured"] is False
    assert qmt["mode"] == "retired"
    summary = gateway_health_summary()
    assert summary[1]["channel"] == CHANNEL_QMT
    assert summary[1]["deprecated"] is True


def test_vnpy_new_route_retired():
    with pytest.raises(VnpyChannelRetired):
        route_vnpy_order(
            order_id=uuid.uuid4(),
            symbol="RB",
            side="buy",
            notional_cny=10000,
        )


def test_qmt_new_route_retired():
    with pytest.raises(QmtChannelRetired):
        route_qmt_order(
            order_id=uuid.uuid4(),
            symbol="AU",
            side="sell",
            notional_cny=25000,
        )


def test_verify_gateway_webhook():
    secret = "test-webhook-secret"
    payload = b'{"external_ref":"QMT-STUB-ABC","status":"filled"}'
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_gateway_webhook(payload, sig, secret) is True
    assert verify_gateway_webhook(payload, "bad", secret) is False
    assert verify_gateway_webhook(payload, sig, "") is False

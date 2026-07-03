"""vn.py 执行适配器测试。"""

import uuid

from engine.execution_adapter import CHANNEL_VNPY, route_vnpy_order


def test_vnpy_stub_without_gateway():
    out = route_vnpy_order(
        order_id=uuid.uuid4(),
        symbol="RB",
        side="buy",
        notional_cny=10000,
    )
    assert out["mode"] == "stub"
    assert out["external_ref"].startswith("VNPY-STUB-")

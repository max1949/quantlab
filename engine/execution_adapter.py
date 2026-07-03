"""执行通道适配 — 纸面 / vn.py Gateway。"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from backend.app.core.config import get_settings

CHANNEL_PAPER = "paper"
CHANNEL_VNPY = "vnpy"


class AdapterError(Exception):
    pass


def vnpy_configured() -> bool:
    return bool(get_settings().vnpy_gateway_url.strip())


def execution_config_payload() -> dict:
    s = get_settings()
    return {
        "kill_switch": s.execution_kill_switch,
        "max_notional_cny": s.execution_max_notional_cny,
        "min_regime_fit_vnpy": s.execution_min_regime_fit_vnpy,
        "vnpy_configured": vnpy_configured(),
        "channels": [
            {"code": CHANNEL_PAPER, "label": "纸面模拟", "available": True},
            {
                "code": CHANNEL_VNPY,
                "label": "vn.py 网关",
                "available": not s.execution_kill_switch,
                "stub_mode": not vnpy_configured(),
            },
        ],
    }


def route_vnpy_order(
    *,
    order_id: uuid.UUID,
    symbol: str,
    side: str,
    notional_cny: float,
    signal_value: float | None = None,
) -> dict[str, Any]:
    """将订单路由到 vn.py Gateway; 未配置网关时走 stub。"""
    settings = get_settings()
    base = settings.vnpy_gateway_url.strip()
    payload = {
        "client_order_id": str(order_id),
        "symbol": symbol,
        "side": side,
        "notional_cny": notional_cny,
        "signal_value": signal_value,
    }

    if not base:
        return {
            "external_ref": f"VNPY-STUB-{order_id.hex[:12].upper()}",
            "mode": "stub",
            "gateway_status": "accepted",
        }

    url = base.rstrip("/") + "/orders"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = settings.vnpy_gateway_token.strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers=headers)
    if resp.status_code not in (200, 201, 202):
        raise AdapterError(f"vn.py 网关拒绝: HTTP {resp.status_code}")
    body = resp.json() if resp.content else {}
    external = body.get("order_id") or body.get("id") or f"VNPY-{order_id.hex[:12].upper()}"
    return {
        "external_ref": str(external),
        "mode": "gateway",
        "gateway_status": body.get("status", "accepted"),
    }

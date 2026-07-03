"""执行通道适配 — 纸面 / vn.py / QMT Gateway。"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from typing import Any

import httpx

from backend.app.core.config import get_settings

CHANNEL_PAPER = "paper"
CHANNEL_VNPY = "vnpy"
CHANNEL_QMT = "qmt"


class AdapterError(Exception):
    pass


def vnpy_configured() -> bool:
    return bool(get_settings().vnpy_gateway_url.strip())


def qmt_configured() -> bool:
    return bool(get_settings().qmt_gateway_url.strip())


def verify_gateway_webhook(payload: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def execution_config_payload() -> dict:
    s = get_settings()
    return {
        "kill_switch": s.execution_kill_switch,
        "max_notional_cny": s.execution_max_notional_cny,
        "min_regime_fit_vnpy": s.execution_min_regime_fit_vnpy,
        "vnpy_configured": vnpy_configured(),
        "qmt_configured": qmt_configured(),
        "channels": [
            {"code": CHANNEL_PAPER, "label": "纸面模拟", "available": True},
            {
                "code": CHANNEL_VNPY,
                "label": "vn.py 网关",
                "available": not s.execution_kill_switch,
                "stub_mode": not vnpy_configured(),
            },
            {
                "code": CHANNEL_QMT,
                "label": "QMT 网关",
                "available": not s.execution_kill_switch,
                "stub_mode": not qmt_configured(),
            },
        ],
    }


def _route_gateway(
    *,
    base_url: str,
    token: str,
    stub_prefix: str,
    order_id: uuid.UUID,
    symbol: str,
    side: str,
    notional_cny: float,
    signal_value: float | None,
) -> dict[str, Any]:
    payload = {
        "client_order_id": str(order_id),
        "symbol": symbol,
        "side": side,
        "notional_cny": notional_cny,
        "signal_value": signal_value,
    }
    base = base_url.strip()
    if not base:
        return {
            "external_ref": f"{stub_prefix}-{order_id.hex[:12].upper()}",
            "mode": "stub",
            "gateway_status": "accepted",
        }

    url = base.rstrip("/") + "/orders"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers=headers)
    if resp.status_code not in (200, 201, 202):
        raise AdapterError(f"网关拒绝: HTTP {resp.status_code}")
    body = resp.json() if resp.content else {}
    external = body.get("order_id") or body.get("id") or f"{stub_prefix}-{order_id.hex[:12].upper()}"
    return {
        "external_ref": str(external),
        "mode": "gateway",
        "gateway_status": body.get("status", "accepted"),
    }


def route_vnpy_order(
    *,
    order_id: uuid.UUID,
    symbol: str,
    side: str,
    notional_cny: float,
    signal_value: float | None = None,
) -> dict[str, Any]:
    s = get_settings()
    return _route_gateway(
        base_url=s.vnpy_gateway_url,
        token=s.vnpy_gateway_token,
        stub_prefix="VNPY-STUB",
        order_id=order_id,
        symbol=symbol,
        side=side,
        notional_cny=notional_cny,
        signal_value=signal_value,
    )


def route_qmt_order(
    *,
    order_id: uuid.UUID,
    symbol: str,
    side: str,
    notional_cny: float,
    signal_value: float | None = None,
) -> dict[str, Any]:
    s = get_settings()
    return _route_gateway(
        base_url=s.qmt_gateway_url,
        token=s.qmt_gateway_token,
        stub_prefix="QMT-STUB",
        order_id=order_id,
        symbol=symbol,
        side=side,
        notional_cny=notional_cny,
        signal_value=signal_value,
    )

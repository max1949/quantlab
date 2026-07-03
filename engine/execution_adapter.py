"""执行通道适配 — 纸面 / vn.py / QMT Gateway。"""

from __future__ import annotations

import hashlib
import hmac
import urllib.parse
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
        "gateway_sync_enabled": s.execution_gateway_sync_enabled,
        "gateway_sync_interval_seconds": s.execution_gateway_sync_interval_seconds,
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


def _gateway_credentials(channel: str) -> tuple[str, str]:
    s = get_settings()
    if channel == CHANNEL_VNPY:
        return s.vnpy_gateway_url, s.vnpy_gateway_token
    if channel == CHANNEL_QMT:
        return s.qmt_gateway_url, s.qmt_gateway_token
    raise AdapterError("非网关通道")


def fetch_gateway_order_status(*, channel: str, external_ref: str) -> str:
    """主动轮询网关订单状态 (GET /orders/{ref})。"""
    base_url, token = _gateway_credentials(channel)
    base = base_url.strip()
    ref = (external_ref or "").strip()
    if not base:
        raise AdapterError("网关未配置, 无法轮询状态")
    if not ref:
        raise AdapterError("缺少 external_ref")

    url = base.rstrip("/") + "/orders/" + urllib.parse.quote(ref, safe="")
    headers: dict[str, str] = {}
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
    if resp.status_code == 404:
        raise AdapterError("网关中找不到该订单")
    if resp.status_code not in (200, 201):
        raise AdapterError(f"网关查询失败: HTTP {resp.status_code}")

    body = resp.json() if resp.content else {}
    status = body.get("status") or body.get("gateway_status")
    if not status:
        raise AdapterError("网关响应缺少 status")
    return str(status)


def probe_gateway_health(channel: str) -> dict[str, Any]:
    """探测执行网关连通性 (GET /health 或 /)。"""
    try:
        base_url, token = _gateway_credentials(channel)
    except AdapterError:
        return {"channel": channel, "configured": False, "ok": None, "mode": "stub"}

    base = base_url.strip()
    if not base:
        return {"channel": channel, "configured": False, "ok": None, "mode": "stub"}

    headers: dict[str, str] = {}
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    last_error = ""
    for path in ("/health", "/"):
        url = base.rstrip("/") + path
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
            if resp.status_code in (200, 204):
                return {
                    "channel": channel,
                    "configured": True,
                    "ok": True,
                    "mode": "gateway",
                    "endpoint": path,
                }
            last_error = f"HTTP {resp.status_code}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)

    return {
        "channel": channel,
        "configured": True,
        "ok": False,
        "mode": "gateway",
        "error": last_error or "unreachable",
    }


def gateway_health_summary() -> list[dict[str, Any]]:
    return [
        probe_gateway_health(CHANNEL_VNPY),
        probe_gateway_health(CHANNEL_QMT),
    ]


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

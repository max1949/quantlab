"""执行通道适配 — 纸面 / QMT Gateway；vn.py 已退役（仅历史审计）。"""

from __future__ import annotations

import hashlib
import hmac
import urllib.parse
import uuid
from typing import Any

import httpx

from backend.app.core.config import get_settings

CHANNEL_PAPER = "paper"
CHANNEL_VNPY = "vnpy"  # VNPY_LEGACY — NEW_CREATE=DENY
CHANNEL_QMT = "qmt"  # QMT_LEGACY — NEW_CREATE=DENY (Phase 5.5)

VNPY_RETIRED_MSG = (
    "vn.py 执行通道已停止新增（VNPY_LEGACY）。"
    "请使用纸面模拟；历史 vn.py 订单仍可查询。"
)
QMT_RETIRED_MSG = (
    "QMT 通道已停止新增（QMT_LEGACY）。"
    "请使用 Nautilus 模拟交易；历史 QMT 订单仍可查询。"
)


class AdapterError(Exception):
    pass


class VnpyChannelRetired(AdapterError):
    """Raised when code attempts a new vn.py create/route."""


class QmtChannelRetired(AdapterError):
    """Raised when code attempts a new QMT create/route."""


def vnpy_configured() -> bool:
    # Phase 5: never advertise as available for new routing.
    return False


def qmt_configured() -> bool:
    # Phase 5.5: never advertise as available for new routing.
    return False


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
        "vnpy_configured": False,
        "vnpy_retired": True,
        "qmt_configured": False,
        "qmt_retired": True,
        "gateway_sync_enabled": s.execution_gateway_sync_enabled,
        "gateway_sync_interval_seconds": s.execution_gateway_sync_interval_seconds,
        "channels": [
            {"code": CHANNEL_PAPER, "label": "纸面模拟", "available": True},
            {
                "code": CHANNEL_VNPY,
                "label": "历史引擎：vn.py（已停止新增，仅保留历史记录）",
                "available": False,
                "deprecated": True,
                "stub_mode": True,
            },
            {
                "code": CHANNEL_QMT,
                "label": "历史通道：QMT（已停止新增，仅保留历史记录）",
                "available": False,
                "deprecated": True,
                "stub_mode": True,
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
        raise VnpyChannelRetired(VNPY_RETIRED_MSG)
    if channel == CHANNEL_QMT:
        raise QmtChannelRetired(QMT_RETIRED_MSG)
    raise AdapterError("非网关通道")


def fetch_gateway_order_status(*, channel: str, external_ref: str) -> str:
    """主动轮询网关订单状态 (GET /orders/{ref})。"""
    if channel == CHANNEL_VNPY:
        raise VnpyChannelRetired(VNPY_RETIRED_MSG)
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
    if channel == CHANNEL_VNPY:
        return {
            "channel": channel,
            "configured": False,
            "ok": False,
            "mode": "retired",
            "deprecated": True,
            "message": VNPY_RETIRED_MSG,
        }
    if channel == CHANNEL_QMT:
        return {
            "channel": channel,
            "configured": False,
            "ok": False,
            "mode": "retired",
            "deprecated": True,
            "message": QMT_RETIRED_MSG,
        }
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
        {
            "channel": CHANNEL_VNPY,
            "configured": False,
            "ok": False,
            "mode": "retired",
            "deprecated": True,
            "message": VNPY_RETIRED_MSG,
        },
        {
            "channel": CHANNEL_QMT,
            "configured": False,
            "ok": False,
            "mode": "retired",
            "deprecated": True,
            "message": QMT_RETIRED_MSG,
        },
    ]


def route_vnpy_order(
    *,
    order_id: uuid.UUID,
    symbol: str,
    side: str,
    notional_cny: float,
    signal_value: float | None = None,
) -> dict[str, Any]:
    raise VnpyChannelRetired(VNPY_RETIRED_MSG)


def route_qmt_order(
    *,
    order_id: uuid.UUID,
    symbol: str,
    side: str,
    notional_cny: float,
    signal_value: float | None = None,
) -> dict[str, Any]:
    raise QmtChannelRetired(QMT_RETIRED_MSG)

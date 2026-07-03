"""Stripe Checkout 适配层 (httpx, 无 stripe SDK 依赖)。"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

import httpx

from backend.app.core.config import get_settings


def stripe_configured() -> bool:
    return bool(get_settings().stripe_secret_key.strip())


def verify_stripe_webhook(payload: bytes, sig_header: str, secret: str) -> bool:
    if not secret or not sig_header:
        return False
    parts: dict[str, list[str]] = {}
    for item in sig_header.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts.setdefault(key, []).append(value)
    timestamps = parts.get("t")
    signatures = parts.get("v1", [])
    if not timestamps:
        return False
    ts = int(timestamps[0])
    if abs(time.time() - ts) > 300:
        return False
    signed = f"{ts}.{payload.decode('utf-8')}"
    expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in signatures)


def create_checkout_session(
    *,
    plan_name: str,
    price_cny: int,
    metadata: dict[str, str],
    success_url: str,
    cancel_url: str,
) -> str:
    settings = get_settings()
    key = settings.stripe_secret_key.strip()
    if not key:
        raise RuntimeError("Stripe 未配置")

    data: dict[str, str] = {
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "cny",
        "line_items[0][price_data][unit_amount]": str(price_cny * 100),
        "line_items[0][price_data][product_data][name]": plan_name,
    }
    for k, v in metadata.items():
        data[f"metadata[{k}]"] = v

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(key, ""),
            data=data,
        )
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
    url = body.get("url")
    if not url:
        raise RuntimeError("Stripe 未返回支付链接")
    return str(url)

"""执行 SLA 告警 Webhook 推送 (机构运维通知)。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
import redis
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.services import execution_compliance_service as ecs

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def alert_fingerprint(alert: dict) -> str:
    return ":".join(
        [
            str(alert.get("code", "")),
            str(alert.get("channel") or ""),
            str(alert.get("order_id") or ""),
        ]
    )


def _redis_client() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def filter_new_alerts(alerts: list[dict]) -> list[dict]:
    """过滤冷却期内已推送过的告警 (Redis SET NX)。"""
    settings = get_settings()
    if not settings.execution_sla_alert_enabled:
        return []
    if not settings.execution_sla_webhook_url.strip():
        return []

    cooldown_sec = max(60, settings.execution_sla_alert_cooldown_minutes * 60)
    fresh: list[dict] = []
    try:
        r = _redis_client()
        for alert in alerts:
            key = f"sla_alert:{alert_fingerprint(alert)}"
            if r.set(key, "1", nx=True, ex=cooldown_sec):
                fresh.append(alert)
    except redis.RedisError as exc:
        logger.warning("sla alert dedup unavailable, sending all: %s", exc)
        return list(alerts)
    return fresh


def dispatch_sla_webhook(db: Session, *, force: bool = False) -> dict:
    """检测 SLA 告警并推送 Webhook。force=True 时跳过冷却去重 (手动测试用)。"""
    settings = get_settings()
    report = ecs.build_global_compliance_report(db, stale_limit=50)
    alerts: list[dict] = list(report.get("sla_alerts") or [])

    if not settings.execution_sla_alert_enabled:
        return {"sent": 0, "skipped": True, "reason": "alerts_disabled", "total_alerts": len(alerts)}

    url = settings.execution_sla_webhook_url.strip()
    if not url:
        return {"sent": 0, "skipped": True, "reason": "webhook_not_configured", "total_alerts": len(alerts)}

    to_send = alerts if force else filter_new_alerts(alerts)
    if not to_send:
        return {
            "sent": 0,
            "skipped": True,
            "reason": "no_new_alerts" if alerts else "no_alerts",
            "total_alerts": len(alerts),
        }

    generated = report.get("generated_at")
    if isinstance(generated, datetime):
        generated_at = generated.isoformat()
    else:
        generated_at = str(generated or _now().isoformat())

    payload = {
        "event": "execution_sla_alert",
        "generated_at": generated_at,
        "alert_count": len(to_send),
        "alerts": to_send,
        "kill_switch": report.get("kill_switch"),
        "sla_stale_minutes": report.get("sla_stale_minutes"),
        "order_summary": report.get("order_summary"),
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()

    return {
        "sent": len(to_send),
        "skipped": False,
        "status_code": resp.status_code,
        "total_alerts": len(alerts),
    }

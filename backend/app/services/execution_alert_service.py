"""执行 SLA 告警 Webhook 推送 (机构运维通知)。"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone

import httpx
import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.organization import ResearchOrg
from backend.app.services import execution_compliance_service as ecs
from backend.app.services.org_service import require_admin

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-QuantLab-Signature"


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


def filter_new_alerts(alerts: list[dict], *, dedup_prefix: str = "global") -> list[dict]:
    """过滤冷却期内已推送过的告警 (Redis SET NX)。"""
    settings = get_settings()
    if not settings.execution_sla_alert_enabled:
        return []

    cooldown_sec = max(60, settings.execution_sla_alert_cooldown_minutes * 60)
    fresh: list[dict] = []
    try:
        r = _redis_client()
        for alert in alerts:
            key = f"sla_alert:{dedup_prefix}:{alert_fingerprint(alert)}"
            if r.set(key, "1", nx=True, ex=cooldown_sec):
                fresh.append(alert)
    except redis.RedisError as exc:
        logger.warning("sla alert dedup unavailable, sending all: %s", exc)
        return list(alerts)
    return fresh


def serialize_webhook_payload(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_webhook_body(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    if not secret.strip() or not signature.strip():
        return False
    expected = sign_webhook_body(body, secret.strip())
    return hmac.compare_digest(expected, signature.strip())


def _post_webhook(url: str, payload: dict, *, secret: str = "") -> int:
    body = serialize_webhook_payload(payload)
    headers = {"Content-Type": "application/json"}
    if secret.strip():
        headers[SIGNATURE_HEADER] = sign_webhook_body(body, secret.strip())
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, content=body, headers=headers)
        resp.raise_for_status()
    return resp.status_code


def _build_payload(report: dict, alerts: list[dict]) -> dict:
    generated = report.get("generated_at")
    if isinstance(generated, datetime):
        generated_at = generated.isoformat()
    else:
        generated_at = str(generated or _now().isoformat())

    payload: dict = {
        "event": "execution_sla_alert",
        "generated_at": generated_at,
        "scope": report.get("scope", "global"),
        "alert_count": len(alerts),
        "alerts": alerts,
        "kill_switch": report.get("kill_switch"),
        "sla_stale_minutes": report.get("sla_stale_minutes"),
        "order_summary": report.get("order_summary"),
    }
    if report.get("org_id"):
        payload["org_id"] = str(report["org_id"])
    return payload


def dispatch_sla_webhook(db: Session, *, force: bool = False) -> dict:
    """检测全局 SLA 告警并推送平台 Webhook。force=True 时跳过冷却去重。"""
    settings = get_settings()
    report = ecs.build_global_compliance_report(db, stale_limit=50)
    alerts: list[dict] = list(report.get("sla_alerts") or [])

    if not settings.execution_sla_alert_enabled:
        return {"sent": 0, "skipped": True, "reason": "alerts_disabled", "total_alerts": len(alerts)}

    url = settings.execution_sla_webhook_url.strip()
    if not url:
        return {"sent": 0, "skipped": True, "reason": "webhook_not_configured", "total_alerts": len(alerts)}

    to_send = alerts if force else filter_new_alerts(alerts, dedup_prefix="global")
    if not to_send:
        return {
            "sent": 0,
            "skipped": True,
            "reason": "no_new_alerts" if alerts else "no_alerts",
            "total_alerts": len(alerts),
        }

    signing_secret = settings.execution_sla_webhook_secret
    status_code = _post_webhook(url, _build_payload(report, to_send), secret=signing_secret)
    return {
        "sent": len(to_send),
        "skipped": False,
        "status_code": status_code,
        "total_alerts": len(alerts),
        "scope": "global",
        "signed": bool(settings.execution_sla_webhook_secret.strip()),
    }


def dispatch_org_sla_webhook(
    db: Session,
    org_id: uuid.UUID,
    *,
    actor_id: uuid.UUID | None = None,
    force: bool = False,
) -> dict:
    """检测机构 SLA 告警并推送到机构配置的 Webhook。"""
    settings = get_settings()
    org = db.get(ResearchOrg, org_id)
    if org is None:
        return {"sent": 0, "skipped": True, "reason": "org_not_found", "org_id": str(org_id)}

    if actor_id is not None:
        require_admin(db, org_id, actor_id)

    url = (org.alert_webhook_url or "").strip()
    if not url:
        return {
            "sent": 0,
            "skipped": True,
            "reason": "webhook_not_configured",
            "org_id": str(org_id),
        }

    if not settings.execution_sla_alert_enabled:
        return {"sent": 0, "skipped": True, "reason": "alerts_disabled", "org_id": str(org_id)}

    report_actor = actor_id or org.owner_id
    report = ecs.build_org_compliance_report(db, org_id, report_actor, stale_limit=30)
    alerts: list[dict] = list(report.get("sla_alerts") or [])

    dedup_prefix = f"org:{org_id}"
    to_send = alerts if force else filter_new_alerts(alerts, dedup_prefix=dedup_prefix)
    if not to_send:
        return {
            "sent": 0,
            "skipped": True,
            "reason": "no_new_alerts" if alerts else "no_alerts",
            "total_alerts": len(alerts),
            "org_id": str(org_id),
        }

    signing_secret = (org.alert_webhook_secret or "").strip() or settings.execution_sla_webhook_secret
    status_code = _post_webhook(url, _build_payload(report, to_send), secret=signing_secret)
    return {
        "sent": len(to_send),
        "skipped": False,
        "status_code": status_code,
        "total_alerts": len(alerts),
        "org_id": str(org_id),
        "scope": "org",
        "signed": bool(signing_secret.strip()),
        "org_secret": bool((org.alert_webhook_secret or "").strip()),
    }


def dispatch_all_org_sla_webhooks(db: Session) -> list[dict]:
    """Celery 定时任务：向所有已配置 Webhook 的机构推送 SLA 告警。"""
    org_ids = list(
        db.execute(
            select(ResearchOrg.id).where(ResearchOrg.alert_webhook_url != "")
        ).scalars().all()
    )
    results: list[dict] = []
    for org_id in org_ids:
        org = db.get(ResearchOrg, org_id)
        if org and (org.alert_webhook_url or "").strip():
            results.append(dispatch_org_sla_webhook(db, org_id, force=False))
    return results

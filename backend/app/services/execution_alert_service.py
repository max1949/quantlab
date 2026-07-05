"""执行 SLA 告警 Webhook 推送 (机构运维通知)。"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.organization import ResearchOrg
from backend.app.models.sla_alert_delivery import SlaAlertDelivery
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


def _mask_webhook_url(url: str) -> str:
    cleaned = (url or "").strip()
    if len(cleaned) <= 48:
        return cleaned
    return "..." + cleaned[-45:]


def _delivery_to_dict(row: SlaAlertDelivery) -> dict:
    return {
        "id": row.id,
        "scope": row.scope,
        "org_id": row.org_id,
        "status": row.status,
        "trigger": row.trigger,
        "alert_count": row.alert_count,
        "skipped_reason": row.skipped_reason,
        "http_status": row.http_status,
        "error_message": row.error_message,
        "webhook_url": row.webhook_url,
        "signed": row.signed,
        "detail": row.detail or {},
        "retry_of_id": row.retry_of_id,
        "created_at": row.created_at,
    }


def record_delivery(
    db: Session,
    *,
    scope: str,
    org_id: uuid.UUID | None,
    status: str,
    trigger: str,
    alert_count: int,
    webhook_url: str = "",
    signed: bool = False,
    skipped_reason: str | None = None,
    http_status: int | None = None,
    error_message: str | None = None,
    detail: dict | None = None,
    retry_of_id: uuid.UUID | None = None,
) -> dict:
    row = SlaAlertDelivery(
        scope=scope,
        org_id=org_id,
        status=status,
        trigger=trigger,
        alert_count=alert_count,
        skipped_reason=skipped_reason,
        http_status=http_status,
        error_message=(error_message or "")[:500] or None,
        webhook_url=_mask_webhook_url(webhook_url),
        signed=signed,
        detail=detail or {},
        retry_of_id=retry_of_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _delivery_to_dict(row)


def list_deliveries(
    db: Session,
    *,
    scope: str | None = None,
    org_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    stmt = select(SlaAlertDelivery).order_by(SlaAlertDelivery.created_at.desc()).limit(min(limit, 200))
    if scope:
        stmt = stmt.where(SlaAlertDelivery.scope == scope)
    if org_id is not None:
        stmt = stmt.where(SlaAlertDelivery.org_id == org_id)
    if status:
        stmt = stmt.where(SlaAlertDelivery.status == status)
    rows = db.execute(stmt).scalars().all()
    return [_delivery_to_dict(r) for r in rows]


def export_org_deliveries_csv(
    db: Session,
    org_id: uuid.UUID,
    *,
    scope: str | None = None,
    limit: int = 500,
) -> str:
    """导出机构 Webhook 投递审计 CSV。"""
    import csv
    import io

    cap = min(limit, 1000)
    if scope == "sla":
        rows = list_deliveries(db, scope="org", org_id=org_id, limit=cap)
    elif scope == "research":
        rows = list_deliveries(db, scope="org_research", org_id=org_id, limit=cap)
    else:
        rows_sla = list_deliveries(db, scope="org", org_id=org_id, limit=limit)
        rows_research = list_deliveries(db, scope="org_research", org_id=org_id, limit=limit)
        rows = sorted(
            rows_sla + rows_research,
            key=lambda r: str(r.get("created_at") or ""),
            reverse=True,
        )[:cap]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "created_at",
            "scope",
            "status",
            "trigger",
            "alert_count",
            "http_status",
            "signed",
            "skipped_reason",
            "error_message",
            "webhook_url",
        ]
    )
    for r in rows:
        created = r.get("created_at")
        writer.writerow(
            [
                created.isoformat() if hasattr(created, "isoformat") else created,
                r.get("scope"),
                r.get("status"),
                r.get("trigger"),
                r.get("alert_count"),
                r.get("http_status"),
                r.get("signed"),
                r.get("skipped_reason") or "",
                r.get("error_message") or "",
                r.get("webhook_url") or "",
            ]
        )
    return buf.getvalue()


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


def _log_skipped(
    db: Session,
    *,
    scope: str,
    org_id: uuid.UUID | None,
    trigger: str,
    reason: str,
    total_alerts: int,
    webhook_url: str = "",
    retry_of_id: uuid.UUID | None = None,
) -> dict:
    delivery = record_delivery(
        db,
        scope=scope,
        org_id=org_id,
        status="skipped",
        trigger=trigger,
        alert_count=0,
        skipped_reason=reason,
        webhook_url=webhook_url,
        detail={"total_alerts": total_alerts},
        retry_of_id=retry_of_id,
    )
    return {
        "sent": 0,
        "skipped": True,
        "reason": reason,
        "total_alerts": total_alerts,
        "scope": scope,
        "org_id": str(org_id) if org_id else None,
        "delivery_id": str(delivery["id"]),
    }


def dispatch_sla_webhook(
    db: Session,
    *,
    force: bool = False,
    trigger: str = "scheduled",
    retry_of_id: uuid.UUID | None = None,
) -> dict:
    """检测全局 SLA 告警并推送平台 Webhook。force=True 时跳过冷却去重。"""
    settings = get_settings()
    report = ecs.build_global_compliance_report(db, stale_limit=50)
    alerts: list[dict] = list(report.get("sla_alerts") or [])

    if not settings.execution_sla_alert_enabled:
        return _log_skipped(
            db,
            scope="global",
            org_id=None,
            trigger=trigger,
            reason="alerts_disabled",
            total_alerts=len(alerts),
            retry_of_id=retry_of_id,
        )

    url = settings.execution_sla_webhook_url.strip()
    if not url:
        return _log_skipped(
            db,
            scope="global",
            org_id=None,
            trigger=trigger,
            reason="webhook_not_configured",
            total_alerts=len(alerts),
            retry_of_id=retry_of_id,
        )

    to_send = alerts if force else filter_new_alerts(alerts, dedup_prefix="global")
    if not to_send:
        return _log_skipped(
            db,
            scope="global",
            org_id=None,
            trigger=trigger,
            reason="no_new_alerts" if alerts else "no_alerts",
            total_alerts=len(alerts),
            webhook_url=url,
            retry_of_id=retry_of_id,
        )

    signing_secret = settings.execution_sla_webhook_secret
    payload = _build_payload(report, to_send)
    try:
        status_code = _post_webhook(url, payload, secret=signing_secret)
    except Exception as exc:
        delivery = record_delivery(
            db,
            scope="global",
            org_id=None,
            status="failed",
            trigger=trigger,
            alert_count=len(to_send),
            webhook_url=url,
            signed=bool(signing_secret.strip()),
            error_message=str(exc),
            detail={"total_alerts": len(alerts), "alert_codes": [a.get("code") for a in to_send]},
            retry_of_id=retry_of_id,
        )
        return {
            "sent": 0,
            "skipped": False,
            "failed": True,
            "error": str(exc),
            "total_alerts": len(alerts),
            "scope": "global",
            "delivery_id": str(delivery["id"]),
        }

    delivery = record_delivery(
        db,
        scope="global",
        org_id=None,
        status="sent",
        trigger=trigger,
        alert_count=len(to_send),
        webhook_url=url,
        signed=bool(signing_secret.strip()),
        http_status=status_code,
        detail={"total_alerts": len(alerts), "alert_codes": [a.get("code") for a in to_send]},
        retry_of_id=retry_of_id,
    )
    return {
        "sent": len(to_send),
        "skipped": False,
        "status_code": status_code,
        "total_alerts": len(alerts),
        "scope": "global",
        "signed": bool(signing_secret.strip()),
        "delivery_id": str(delivery["id"]),
    }


def dispatch_org_sla_webhook(
    db: Session,
    org_id: uuid.UUID,
    *,
    actor_id: uuid.UUID | None = None,
    force: bool = False,
    trigger: str = "manual",
    retry_of_id: uuid.UUID | None = None,
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
        return _log_skipped(
            db,
            scope="org",
            org_id=org_id,
            trigger=trigger,
            reason="webhook_not_configured",
            total_alerts=0,
            retry_of_id=retry_of_id,
        )

    if not settings.execution_sla_alert_enabled:
        return _log_skipped(
            db,
            scope="org",
            org_id=org_id,
            trigger=trigger,
            reason="alerts_disabled",
            total_alerts=0,
            webhook_url=url,
            retry_of_id=retry_of_id,
        )

    report_actor = actor_id or org.owner_id
    report = ecs.build_org_compliance_report(db, org_id, report_actor, stale_limit=30)
    alerts: list[dict] = list(report.get("sla_alerts") or [])

    dedup_prefix = f"org:{org_id}"
    to_send = alerts if force else filter_new_alerts(alerts, dedup_prefix=dedup_prefix)
    if not to_send:
        return _log_skipped(
            db,
            scope="org",
            org_id=org_id,
            trigger=trigger,
            reason="no_new_alerts" if alerts else "no_alerts",
            total_alerts=len(alerts),
            webhook_url=url,
            retry_of_id=retry_of_id,
        )

    signing_secret = (org.alert_webhook_secret or "").strip() or settings.execution_sla_webhook_secret
    payload = _build_payload(report, to_send)
    try:
        status_code = _post_webhook(url, payload, secret=signing_secret)
    except Exception as exc:
        delivery = record_delivery(
            db,
            scope="org",
            org_id=org_id,
            status="failed",
            trigger=trigger,
            alert_count=len(to_send),
            webhook_url=url,
            signed=bool(signing_secret.strip()),
            error_message=str(exc),
            detail={"total_alerts": len(alerts), "alert_codes": [a.get("code") for a in to_send]},
            retry_of_id=retry_of_id,
        )
        return {
            "sent": 0,
            "skipped": False,
            "failed": True,
            "error": str(exc),
            "total_alerts": len(alerts),
            "org_id": str(org_id),
            "scope": "org",
            "delivery_id": str(delivery["id"]),
        }

    delivery = record_delivery(
        db,
        scope="org",
        org_id=org_id,
        status="sent",
        trigger=trigger,
        alert_count=len(to_send),
        webhook_url=url,
        signed=bool(signing_secret.strip()),
        http_status=status_code,
        detail={"total_alerts": len(alerts), "alert_codes": [a.get("code") for a in to_send]},
        retry_of_id=retry_of_id,
    )
    return {
        "sent": len(to_send),
        "skipped": False,
        "status_code": status_code,
        "total_alerts": len(alerts),
        "org_id": str(org_id),
        "scope": "org",
        "signed": bool(signing_secret.strip()),
        "org_secret": bool((org.alert_webhook_secret or "").strip()),
        "delivery_id": str(delivery["id"]),
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
            results.append(
                dispatch_org_sla_webhook(db, org_id, force=False, trigger="scheduled")
            )
    return results


def retry_failed_deliveries(
    db: Session,
    *,
    hours: int = 24,
    limit: int = 20,
    scope: str | None = None,
    org_id: uuid.UUID | None = None,
) -> dict:
    """重试近期失败的 SLA 投递 (按 scope/org 去重后 force 推送)。"""
    since = _now() - timedelta(hours=max(1, hours))
    conditions = [
        SlaAlertDelivery.status == "failed",
        SlaAlertDelivery.created_at >= since,
    ]
    if scope:
        conditions.append(SlaAlertDelivery.scope == scope)
    if org_id:
        conditions.append(SlaAlertDelivery.org_id == org_id)
    rows = list(
        db.execute(
            select(SlaAlertDelivery)
            .where(*conditions)
            .order_by(SlaAlertDelivery.created_at.desc())
            .limit(min(limit, 100))
        ).scalars().all()
    )
    seen: set[str] = set()
    results: list[dict] = []
    for row in rows:
        key = f"{row.scope}:{row.org_id or 'global'}"
        if key in seen:
            continue
        seen.add(key)
        if row.scope == "org" and row.org_id:
            results.append(
                dispatch_org_sla_webhook(
                    db,
                    row.org_id,
                    force=True,
                    trigger="retry",
                    retry_of_id=row.id,
                )
            )
        elif row.scope == "org_research" and row.org_id:
            from backend.app.services import org_attention_service as oas

            results.append(
                oas.dispatch_org_research_attention_webhook(
                    db,
                    row.org_id,
                    force=True,
                    trigger="retry",
                    retry_of_id=row.id,
                )
            )
        elif row.scope == "global":
            results.append(
                dispatch_sla_webhook(
                    db,
                    force=True,
                    trigger="retry",
                    retry_of_id=row.id,
                )
            )
    return {"retried": len(results), "results": results}

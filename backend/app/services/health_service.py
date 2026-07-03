"""就绪探针 — DB / Redis / Celery 连通性 (机构运维)。"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings


def check_database(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def check_redis() -> dict:
    try:
        import redis

        r = redis.from_url(get_settings().redis_url, decode_responses=True)
        r.ping()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def check_celery() -> dict:
    """尽力探测 worker 是否在线 (非阻塞)。"""
    try:
        from backend.tasks.celery_app import celery_app

        replies = celery_app.control.ping(timeout=1.0)
        if replies:
            return {"ok": True, "workers": len(replies)}
        return {"ok": False, "error": "no workers responded"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def readiness(db: Session) -> dict:
    db_status = check_database(db)
    redis_status = check_redis()
    celery_status = check_celery()
    ok = db_status["ok"] and redis_status["ok"]
    return {
        "status": "ready" if ok else "degraded",
        "database": db_status,
        "redis": redis_status,
        "celery": celery_status,
    }

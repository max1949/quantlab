"""科学验证 Celery 任务 (Sprint 5)。

与回测任务同构: API 入队, worker 执行重计算, 自行开启 DB 会话。
"""

from __future__ import annotations

from backend.app.core.database import SessionLocal
from backend.app.tasks.celery_app import celery_app


@celery_app.task(name="quantlab.run_validation")
def run_validation_task(validation_id: str) -> str:
    from backend.app.services import validation_service

    db = SessionLocal()
    try:
        validation_service.execute(db, validation_id)
    finally:
        db.close()
    return validation_id

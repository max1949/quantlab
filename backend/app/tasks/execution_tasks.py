"""执行网关定时同步 Celery 任务。"""

from __future__ import annotations

from backend.app.core.database import SessionLocal
from backend.app.tasks.celery_app import celery_app


@celery_app.task(name="quantlab.sync_gateway_orders")
def sync_gateway_orders_task() -> dict:
    from backend.app.services import execution_service as exs

    db = SessionLocal()
    try:
        return exs.sync_all_pending_gateway_orders(db)
    finally:
        db.close()


@celery_app.task(name="quantlab.check_execution_sla_alerts")
def check_execution_sla_alerts_task() -> dict:
    from backend.app.services import execution_alert_service as eas

    db = SessionLocal()
    try:
        return eas.dispatch_sla_webhook(db, force=False)
    finally:
        db.close()

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
        global_result = eas.dispatch_sla_webhook(db, force=False)
        org_results = eas.dispatch_all_org_sla_webhooks(db)
        return {"global": global_result, "orgs": org_results}
    finally:
        db.close()

"""Celery 应用 (异步计算层)。

重计算与 API 解耦: 回测等任务在 worker 进程执行。任务模块通过 include 注册,
worker 启动时即可发现 (Sprint 4 起: 回测; 后续增补验证 / 因子计算)。
"""

from celery import Celery

from backend.app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "quantlab",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.app.tasks.backtest_tasks",
        "backend.app.tasks.validation_tasks",
        "backend.app.tasks.paper_tracking_tasks",
        "backend.app.tasks.execution_tasks",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=settings.celery_task_always_eager,
)

if settings.execution_gateway_sync_enabled and not settings.celery_task_always_eager:
    celery_app.conf.beat_schedule = {
        "sync-gateway-orders": {
            "task": "quantlab.sync_gateway_orders",
            "schedule": float(settings.execution_gateway_sync_interval_seconds),
            "options": {"expires": max(60, settings.execution_gateway_sync_interval_seconds - 30)},
        },
    }
    if settings.execution_sla_alert_enabled and settings.execution_sla_webhook_url.strip():
        celery_app.conf.beat_schedule["check-execution-sla-alerts"] = {
            "task": "quantlab.check_execution_sla_alerts",
            "schedule": float(settings.execution_sla_alert_interval_seconds),
            "options": {"expires": max(60, settings.execution_sla_alert_interval_seconds - 30)},
        }

"""Celery 应用 (异步计算层)。

骨架阶段仅完成 Celery 实例装配, 真实任务 (回测 / 验证 / 因子计算)
从 Sprint 4 起在 backend/app/tasks/ 下定义并注册。
"""

from celery import Celery

from backend.app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "quantlab",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

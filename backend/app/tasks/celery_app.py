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
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=settings.celery_task_always_eager,
)

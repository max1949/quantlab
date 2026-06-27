"""回测 Celery 任务 (Sprint 4)。

重计算与 API 解耦: API 只创建回测并入队, 真正的计算在 worker 进程执行。
任务自行开启 DB 会话 (不复用请求会话)。
"""

from __future__ import annotations

from backend.app.core.database import SessionLocal
from backend.app.tasks.celery_app import celery_app


@celery_app.task(name="quantlab.run_backtest")
def run_backtest_task(backtest_id: str) -> str:
    # 延迟导入避免 celery_app 装配期的循环依赖
    from backend.app.services import backtest_service

    db = SessionLocal()
    try:
        backtest_service.execute(db, backtest_id)
    finally:
        db.close()
    return backtest_id

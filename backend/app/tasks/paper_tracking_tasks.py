"""每日纸面跟踪 Celery 任务。"""

from __future__ import annotations

from backend.app.core.database import SessionLocal
from backend.app.tasks.celery_app import celery_app


@celery_app.task(name="quantlab.daily_paper_snapshot")
def daily_paper_snapshot_task() -> dict:
    from backend.app.services import paper_tracking_service as pts

    db = SessionLocal()
    try:
        return pts.run_daily_paper_batch(db)
    finally:
        db.close()

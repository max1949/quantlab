"""学院任务事件钩子 — 研究动作成功后自动结算 XP (幂等)。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services import task_service


def _collect(db: Session, user: User, codes: list[str]) -> list[dict]:
    rewards: list[dict] = []
    for code in codes:
        result = task_service.try_auto_complete(db, user, code)
        if result is None:
            continue
        task = result["task"]
        rewards.append(
            {
                "code": code,
                "title": task.title,
                "awarded_xp": result["awarded_xp"],
                "leveled_up": result["leveled_up"],
            }
        )
    return rewards


def on_factor_preview(db: Session, user: User) -> list[dict]:
    return _collect(db, user, ["first-observation"])


def on_backtest_success(db: Session, user: User) -> list[dict]:
    return _collect(db, user, ["first-observation", "first-backtest"])


def on_validation_success(db: Session, user: User) -> list[dict]:
    return _collect(db, user, ["first-validation"])


def on_welcome(db: Session, user: User) -> list[dict]:
    return _collect(db, user, ["welcome"])


def on_report_generated(db: Session, user: User) -> list[dict]:
    return _collect(db, user, ["first-report"])


def on_project_published(db: Session, user: User) -> list[dict]:
    return _collect(db, user, ["first-publish"])

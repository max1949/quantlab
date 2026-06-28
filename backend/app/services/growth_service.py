"""Growth OS 共享服务 (Sprint 9A): 埋点 / 两套分数 / 漏斗。

两套互不合并的分数 (核心设计):
- ``reward_points`` (游戏激励): 完成里程碑、邀请激活、分享等"行为"奖励。可快速累积, 鼓励参与。
- ``research_contribution_score`` (研究信用): 由真实研究产物质量沉淀, 不被游戏行为稀释 ->
  这是平台真正想衡量的"研究贡献", 用于"Top Researcher"等长期榜单。

竞技的 ``research_score`` (Sprint 6) 仍独立保留 (历史最佳 Research Score)。
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.growth import UserEvent
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus

# 研究信用权重 (产物质量沉淀)。
W_EFFECTIVE_VALIDATION = 10.0
W_REPORT = 8.0
W_PUBLISHED_PROJECT = 5.0
W_FOLLOWER = 2.0

EFFECTIVE_GRADES = {"稳健", "中等"}


def log_event(
    db: Session, event: str, user_id: uuid.UUID | None = None, props: dict | None = None
) -> UserEvent:
    """记录埋点事件 (匿名允许 user_id=None)。"""
    ev = UserEvent(user_id=user_id, event=event, props=props or {})
    db.add(ev)
    db.commit()
    return ev


def award_reward_points(db: Session, user: User, points: int, *, commit: bool = True) -> int:
    """发放游戏激励积分, 返回累计值。"""
    if points <= 0:
        return user.reward_points
    user.reward_points = (user.reward_points or 0) + points
    if commit:
        db.commit()
        db.refresh(user)
    return user.reward_points


def _count(db: Session, stmt) -> int:
    return int(db.execute(stmt).scalar_one() or 0)


def _followers_count(db: Session, uid: uuid.UUID) -> int:
    # 延迟导入避免与 social 服务循环。
    from backend.app.models.growth import UserFollow

    return _count(db, select(func.count(UserFollow.id)).where(UserFollow.followee_id == uid))


def recompute_contribution_score(db: Session, user: User, *, commit: bool = True) -> float:
    """由用户的研究产物质量重算研究信用分 (不含任何游戏行为)。"""
    uid = user.id

    effective = 0
    robustness_rows = db.execute(
        select(Validation.robustness).where(
            Validation.owner_id == uid,
            Validation.status == ValidationStatus.SUCCESS.value,
        )
    ).scalars().all()
    for rob in robustness_rows:
        if (rob or {}).get("grade") in EFFECTIVE_GRADES:
            effective += 1

    reports = _count(db, select(func.count(ResearchReport.id)).where(ResearchReport.owner_id == uid))
    published = _count(
        db,
        select(func.count(ResearchProject.id)).where(
            ResearchProject.owner_id == uid,
            ResearchProject.status == ProjectStatus.PUBLISHED.value,
        ),
    )
    followers = _followers_count(db, uid)

    score = (
        W_EFFECTIVE_VALIDATION * effective
        + W_REPORT * reports
        + W_PUBLISHED_PROJECT * published
        + W_FOLLOWER * followers
    )
    user.research_contribution_score = round(score, 2)
    if commit:
        db.commit()
        db.refresh(user)
    return user.research_contribution_score


def funnel(db: Session) -> dict:
    """基础增长漏斗: 按事件计数 (去重用户)。"""
    stages = ["visit", "register", "choose_type", "create_project", "run_backtest", "generate_report", "share"]
    out = []
    for ev in stages:
        users = _count(
            db, select(func.count(func.distinct(UserEvent.user_id))).where(UserEvent.event == ev)
        )
        total = _count(db, select(func.count(UserEvent.id)).where(UserEvent.event == ev))
        out.append({"stage": ev, "users": users, "events": total})
    return {"funnel": out}

"""关注关系 + 关注 Feed (Sprint 9A)。

类 GitHub 的 Follow: 形成研究员之间的关注网络, 关注 Feed 让用户因"人"而留存。
被关注数计入研究信用分 -> 优质研究者获得网络放大。
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.growth import UserFollow
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.services import growth_service


class CannotFollowSelfError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def follow(db: Session, follower: User, followee_id: uuid.UUID) -> bool:
    """关注 (幂等)。返回是否新建。"""
    if follower.id == followee_id:
        raise CannotFollowSelfError
    followee = db.get(User, followee_id)
    if followee is None:
        raise UserNotFoundError(str(followee_id))
    existing = db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == follower.id, UserFollow.followee_id == followee_id
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    db.add(UserFollow(follower_id=follower.id, followee_id=followee_id))
    db.commit()
    growth_service.recompute_contribution_score(db, followee)
    growth_service.log_event(db, "follow", follower.id, {"followee_id": str(followee_id)})
    return True


def unfollow(db: Session, follower: User, followee_id: uuid.UUID) -> bool:
    existing = db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == follower.id, UserFollow.followee_id == followee_id
        )
    ).scalar_one_or_none()
    if existing is None:
        return False
    db.delete(existing)
    db.commit()
    followee = db.get(User, followee_id)
    if followee is not None:
        growth_service.recompute_contribution_score(db, followee)
    return True


def counts(db: Session, user_id: uuid.UUID) -> dict:
    followers = int(
        db.execute(select(func.count(UserFollow.id)).where(UserFollow.followee_id == user_id)).scalar_one() or 0
    )
    following = int(
        db.execute(select(func.count(UserFollow.id)).where(UserFollow.follower_id == user_id)).scalar_one() or 0
    )
    return {"followers": followers, "following": following}


def is_following(db: Session, follower_id: uuid.UUID, followee_id: uuid.UUID) -> bool:
    return db.execute(
        select(UserFollow.id).where(
            UserFollow.follower_id == follower_id, UserFollow.followee_id == followee_id
        )
    ).first() is not None


def following_target_ids(
    db: Session, follower_id: uuid.UUID, followee_ids: list[uuid.UUID]
) -> set[uuid.UUID]:
    """批量查询 viewer 已关注的 owner_id 集合。"""
    if not followee_ids:
        return set()
    rows = db.execute(
        select(UserFollow.followee_id).where(
            UserFollow.follower_id == follower_id,
            UserFollow.followee_id.in_(followee_ids),
        )
    ).scalars().all()
    return set(rows)


def feed(db: Session, follower_id: uuid.UUID, limit: int = 30) -> list[ResearchReport]:
    """我关注的研究员的最新公开研究报告。"""
    followee_ids = list(
        db.execute(
            select(UserFollow.followee_id).where(UserFollow.follower_id == follower_id)
        ).scalars().all()
    )
    if not followee_ids:
        return []
    return list(
        db.execute(
            select(ResearchReport)
            .where(
                ResearchReport.owner_id.in_(followee_ids),
                ResearchReport.is_public.is_(True),
            )
            .order_by(ResearchReport.created_at.desc())
            .limit(limit)
        ).scalars().all()
    )

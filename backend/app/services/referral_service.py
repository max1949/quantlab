"""邀请裂变 (Sprint 9A)。

邀请码 = 邀请人 username。被邀请者注册时记一行 (registered); 完成首次研究后激活,
给邀请人发放 reward_points (游戏激励, 不污染研究信用分)。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.growth import Referral, ReferralStatus
from backend.app.models.user import User
from backend.app.services import growth_service

REFERRAL_ACTIVATION_REWARD = 50  # 被邀请者完成首次研究, 邀请人得 50 reward_points


def link_referral(db: Session, invitee: User, ref_code: str) -> Referral | None:
    """注册时调用: 按邀请码 (referrer username) 关联邀请关系。无效/自荐则忽略。"""
    if not ref_code:
        return None
    referrer = db.execute(select(User).where(User.username == ref_code)).scalar_one_or_none()
    if referrer is None or referrer.id == invitee.id:
        return None
    invitee.referred_by = referrer.id
    ref = Referral(
        referrer_id=referrer.id, invitee_id=invitee.id, status=ReferralStatus.REGISTERED.value
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


def activate_if_referred(db: Session, invitee: User) -> bool:
    """被邀请者完成首个研究产物时调用 (幂等)。激活则给邀请人发奖, 返回是否本次激活。"""
    if invitee.referred_by is None:
        return False
    ref = db.execute(
        select(Referral).where(Referral.invitee_id == invitee.id)
    ).scalar_one_or_none()
    if ref is None or ref.status == ReferralStatus.ACTIVATED.value:
        return False
    ref.status = ReferralStatus.ACTIVATED.value
    ref.reward_points = REFERRAL_ACTIVATION_REWARD
    ref.activated_at = datetime.now(timezone.utc)
    referrer = db.get(User, ref.referrer_id)
    if referrer is not None:
        growth_service.award_reward_points(db, referrer, REFERRAL_ACTIVATION_REWARD, commit=False)
    db.commit()
    growth_service.log_event(
        db, "referral_activated", referrer.id if referrer else None,
        {"invitee_id": str(invitee.id)},
    )
    return True


def my_referral(db: Session, user: User) -> dict:
    """我的邀请战绩。"""
    invited = int(
        db.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user.id)
        ).scalar_one() or 0
    )
    activated = int(
        db.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user.id,
                Referral.status == ReferralStatus.ACTIVATED.value,
            )
        ).scalar_one() or 0
    )
    earned = int(
        db.execute(
            select(func.coalesce(func.sum(Referral.reward_points), 0)).where(
                Referral.referrer_id == user.id
            )
        ).scalar_one() or 0
    )
    return {
        "code": user.username,
        "share_path": f"/?ref={user.username}",
        "invited": invited,
        "activated": activated,
        "reward_points_earned": earned,
    }

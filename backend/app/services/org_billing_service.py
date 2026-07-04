"""机构团队订阅与计费。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.membership import RedeemCode
from backend.app.models.organization import OrgMember, OrgSubscription, ResearchOrg
from backend.app.services import membership_service as ms
from backend.app.services import payment_service
from backend.app.services.org_service import OrgAccessDeniedError, require_admin

_SUB_ACTIVE = "active"


class OrgBillingError(Exception):
    pass


class OrgSeatLimitError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _active_org_subs(db: Session, org_id: uuid.UUID) -> list[OrgSubscription]:
    now = _now()
    rows = list(
        db.execute(
            select(OrgSubscription).where(
                OrgSubscription.org_id == org_id,
                OrgSubscription.status == _SUB_ACTIVE,
            )
        ).scalars().all()
    )
    return [
        s for s in rows if s.expires_at is None or _normalize_utc(s.expires_at) > now
    ]


# 未付费机构的免费席位额度 (含所有者本人)。
FREE_SEATS = 3


def org_tier(db: Session, org_id: uuid.UUID) -> int:
    subs = _active_org_subs(db, org_id)
    return max((s.tier for s in subs), default=ms.TIER_FREE)


def org_seat_limit(db: Session, org_id: uuid.UUID) -> int:
    """机构当前席位上限 = 未过期团队订阅里的最大 seats; 无付费则免费额度。"""
    subs = _active_org_subs(db, org_id)
    return max((s.seats for s in subs), default=FREE_SEATS)


def org_seat_usage(db: Session, org_id: uuid.UUID) -> int:
    return int(
        db.execute(
            select(func.count()).select_from(OrgMember).where(OrgMember.org_id == org_id)
        ).scalar_one()
        or 0
    )


def ensure_seat_available(db: Session, org_id: uuid.UUID, *, adding: int = 1) -> None:
    """成员数 + 拟新增是否超过席位上限; 超过则抛 OrgSeatLimitError。"""
    limit = org_seat_limit(db, org_id)
    used = org_seat_usage(db, org_id)
    if used + adding > limit:
        raise OrgSeatLimitError(
            f"团队席位已满 ({used}/{limit})，请升级团队套餐以增加席位。"
        )


def org_tiers_for_user(db: Session, user_id: uuid.UUID) -> int:
    org_ids = db.execute(
        select(OrgMember.org_id).where(OrgMember.user_id == user_id)
    ).scalars().all()
    if not org_ids:
        return ms.TIER_FREE
    return max(org_tier(db, oid) for oid in org_ids)


def grant_org_subscription(
    db: Session,
    org_id: uuid.UUID,
    *,
    tier: int,
    period_days: int,
    plan_code: str,
    seats: int,
    source: str = "redeem",
    stripe_session_id: str | None = None,
    actor_id: uuid.UUID | None = None,
) -> OrgSubscription:
    expires = None if period_days <= 0 else _now() + timedelta(days=period_days)
    sub = OrgSubscription(
        org_id=org_id,
        plan_code=plan_code,
        tier=tier,
        seats=seats,
        status=_SUB_ACTIVE,
        source=source,
        expires_at=expires,
        stripe_session_id=stripe_session_id,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    from backend.app.services import billing_ledger_service as bls

    bls.record_org_subscription(
        db,
        org_id=org_id,
        actor_id=actor_id,
        plan_code=plan_code,
        tier=tier,
        seats=seats,
        source=source,
        subscription_id=sub.id,
        expires_at=sub.expires_at,
        stripe_session_id=stripe_session_id,
    )
    return sub


def get_org_billing(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    require_admin(db, org_id, user_id)
    org = db.get(ResearchOrg, org_id)
    if org is None:
        raise OrgAccessDeniedError(str(org_id))

    subs = _active_org_subs(db, org_id)
    tier = max((s.tier for s in subs), default=ms.TIER_FREE)
    primary = None
    if subs:
        primary = sorted(
            subs, key=lambda s: (s.tier, s.expires_at or datetime.max.replace(tzinfo=timezone.utc))
        )[-1]

    member_count = org_seat_usage(db, org_id)
    seats = org_seat_limit(db, org_id)

    team_plans = [p for p in ms.PLANS if p.get("kind") == "org"]
    return {
        "org_id": org_id,
        "org_name": org.name,
        "tier": tier,
        "tier_name": ms.TIER_NAMES.get(tier, "免费"),
        "plan_code": primary.plan_code if primary else "free",
        "expires_at": primary.expires_at if primary else None,
        "seats": seats,
        "member_count": member_count,
        "is_paid": tier > 0,
        "team_plans": team_plans,
    }


def redeem_org_code(
    db: Session, org_id: uuid.UUID, user_id: uuid.UUID, code: str
) -> OrgSubscription:
    org = db.get(ResearchOrg, org_id)
    if org is None:
        raise OrgBillingError("机构不存在")
    if org.owner_id != user_id:
        raise OrgBillingError("仅机构所有者可兑换团队套餐")

    code = (code or "").strip().upper()
    if not code:
        raise OrgBillingError("兑换码不能为空")

    rc = db.execute(select(RedeemCode).where(RedeemCode.code == code)).scalar_one_or_none()
    if rc is None:
        raise OrgBillingError("兑换码无效")
    if rc.kind != "org":
        raise OrgBillingError("该兑换码不是团队套餐码")
    if rc.used_by is not None:
        raise OrgBillingError("兑换码已被使用")

    plan = ms.PLAN_BY_CODE.get(rc.plan_code)
    seats = rc.seats or (plan.get("seats", 5) if plan else 5)

    rc.used_by = user_id
    rc.used_at = _now()
    db.add(rc)
    return grant_org_subscription(
        db,
        org_id,
        tier=rc.tier,
        period_days=rc.period_days,
        plan_code=rc.plan_code,
        seats=seats,
        source="redeem",
        actor_id=user_id,
    )


def start_org_checkout(
    db: Session, org_id: uuid.UUID, user_id: uuid.UUID, plan_code: str
) -> dict:
    org = db.get(ResearchOrg, org_id)
    if org is None:
        raise OrgBillingError("机构不存在")
    if org.owner_id != user_id:
        raise OrgBillingError("仅机构所有者可购买团队套餐")

    plan = ms.PLAN_BY_CODE.get(plan_code)
    if plan is None or plan.get("kind") != "org":
        raise OrgBillingError("无效的团队套餐")

    base = {
        "plan_code": plan_code,
        "plan_name": plan["name"],
        "price_cny": plan["price_cny"],
        "org_id": str(org_id),
    }

    if not payment_service.stripe_configured():
        return {
            **base,
            "configured": False,
            "pay_url": None,
            "message": "在线支付尚未开通，请联系运营获取团队兑换码，在机构页下方兑换。",
        }

    from backend.app.services.membership_service import frontend_origin

    origin = frontend_origin()
    pay_url = payment_service.create_checkout_session(
        plan_name=plan["name"],
        price_cny=plan["price_cny"],
        metadata={
            "kind": "org",
            "org_id": str(org_id),
            "plan_code": plan_code,
            "user_id": str(user_id),
        },
        success_url=f"{origin}/orgs/{org_id}?checkout=success",
        cancel_url=f"{origin}/orgs/{org_id}?checkout=cancel",
    )
    return {
        **base,
        "configured": True,
        "pay_url": pay_url,
        "message": "正在跳转支付…",
    }


def fulfill_checkout_session(
    db: Session,
    *,
    kind: str,
    plan_code: str,
    user_id: uuid.UUID | None,
    org_id: uuid.UUID | None,
    stripe_session_id: str | None,
) -> None:
    plan = ms.PLAN_BY_CODE.get(plan_code)
    if plan is None or plan["tier"] == 0:
        return

    if kind == "org":
        if org_id is None:
            return
        if stripe_session_id:
            existing = db.execute(
                select(OrgSubscription).where(OrgSubscription.stripe_session_id == stripe_session_id)
            ).scalar_one_or_none()
            if existing is not None:
                return
        grant_org_subscription(
            db,
            org_id,
            tier=plan["tier"],
            period_days=plan["period_days"],
            plan_code=plan_code,
            seats=plan.get("seats", 5),
            source="checkout",
            stripe_session_id=stripe_session_id,
            actor_id=user_id,
        )
        return

    if user_id is None:
        return
    from backend.app.models.user import User

    user = db.get(User, user_id)
    if user is None:
        return
    if stripe_session_id:
        from backend.app.models.membership import Subscription

        existing = db.execute(
            select(Subscription).where(Subscription.stripe_session_id == stripe_session_id)
        ).scalar_one_or_none()
        if existing is not None:
            return
    ms.grant(
        db,
        user,
        plan["tier"],
        plan["period_days"],
        plan_code,
        source="checkout",
        stripe_session_id=stripe_session_id,
    )

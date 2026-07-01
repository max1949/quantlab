"""会员 / 计费路由 (Sprint 10 商业化)。

- GET  /billing/plans         套餐目录 (公开)
- GET  /billing/me            我的订阅状态
- GET  /billing/entitlements  我的全部功能权益 (前端据此显示锁/解锁)
- POST /billing/redeem        兑换码开通
- POST /billing/checkout      在线支付下单 (占位, 待接商户号)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.membership import (
    CheckoutIn,
    CheckoutOut,
    EntitlementsOut,
    PlanOut,
    RedeemIn,
    RedeemOut,
    SubscriptionStatusOut,
)
from backend.app.services import membership_service as ms

router = APIRouter()


@router.get("/plans", response_model=list[PlanOut], summary="套餐目录")
def list_plans() -> list[PlanOut]:
    return [PlanOut(**p) for p in ms.PLANS]


@router.get("/me", response_model=SubscriptionStatusOut, summary="我的订阅状态")
def my_subscription(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> SubscriptionStatusOut:
    return SubscriptionStatusOut(**ms.get_status(db, current_user))


@router.get("/entitlements", response_model=EntitlementsOut, summary="我的功能权益")
def my_entitlements(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> EntitlementsOut:
    return EntitlementsOut(**ms.entitlements(db, current_user))


@router.post("/redeem", response_model=RedeemOut, summary="兑换码开通会员")
def redeem(
    payload: RedeemIn,
    current_user: CurrentUser,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> RedeemOut:
    from backend.app.core.request_ip import get_client_ip
    from backend.app.services import rate_limit

    try:
        rate_limit.check_redeem(get_client_ip(request), str(current_user.id))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    try:
        sub = ms.redeem(db, current_user, payload.code)
    except ms.RedeemError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return RedeemOut(
        ok=True,
        tier=sub.tier,
        tier_name=ms.TIER_NAMES.get(sub.tier, "免费"),
        expires_at=sub.expires_at,
        message=f"已开通「{ms.TIER_NAMES.get(sub.tier, '免费')}」会员",
    )


@router.post("/checkout", response_model=CheckoutOut, summary="在线支付下单 (占位)")
def checkout(
    payload: CheckoutIn,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CheckoutOut:
    try:
        result = ms.start_checkout(db, current_user, payload.plan_code)
    except ms.RedeemError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return CheckoutOut(**result)

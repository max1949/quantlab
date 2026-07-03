"""计费流水 — 机构团队与个人订阅审计。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.billing_ledger import BillingLedger
from backend.app.services import membership_service as ms
from backend.app.services.org_service import OrgAccessDeniedError, require_admin


def _plan_meta(plan_code: str) -> tuple[str, float]:
    plan = ms.PLAN_BY_CODE.get(plan_code)
    if plan is None:
        return plan_code, 0.0
    return str(plan.get("name", plan_code)), float(plan.get("price_cny", 0))


def record_org_subscription(
    db: Session,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    plan_code: str,
    tier: int,
    seats: int,
    source: str,
    subscription_id: uuid.UUID,
    expires_at: datetime | None,
    stripe_session_id: str | None = None,
) -> BillingLedger:
    plan_name, amount = _plan_meta(plan_code)
    row = BillingLedger(
        scope="org",
        event=source if source in ("redeem", "checkout") else "grant",
        org_id=org_id,
        actor_id=actor_id,
        plan_code=plan_code,
        plan_name=plan_name,
        tier=tier,
        seats=seats,
        amount_cny=amount,
        source=source,
        stripe_session_id=stripe_session_id,
        subscription_ref=subscription_id,
        expires_at=expires_at,
        detail=f"团队套餐 {plan_name}",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def record_personal_subscription(
    db: Session,
    *,
    user_id: uuid.UUID,
    plan_code: str,
    tier: int,
    source: str,
    subscription_id: uuid.UUID,
    expires_at: datetime | None,
    stripe_session_id: str | None = None,
) -> BillingLedger:
    plan_name, amount = _plan_meta(plan_code)
    row = BillingLedger(
        scope="personal",
        event=source if source in ("redeem", "checkout") else "grant",
        user_id=user_id,
        actor_id=user_id,
        plan_code=plan_code,
        plan_name=plan_name,
        tier=tier,
        amount_cny=amount,
        source=source,
        stripe_session_id=stripe_session_id,
        subscription_ref=subscription_id,
        expires_at=expires_at,
        detail=f"个人套餐 {plan_name}",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ledger_to_dict(row: BillingLedger) -> dict:
    return {
        "id": row.id,
        "scope": row.scope,
        "event": row.event,
        "org_id": row.org_id,
        "plan_code": row.plan_code,
        "plan_name": row.plan_name,
        "tier": row.tier,
        "tier_name": ms.TIER_NAMES.get(row.tier, "免费"),
        "seats": row.seats,
        "amount_cny": float(row.amount_cny),
        "currency": row.currency,
        "source": row.source,
        "stripe_session_id": row.stripe_session_id,
        "expires_at": row.expires_at,
        "detail": row.detail,
        "created_at": row.created_at,
    }


def list_org_billing_history(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, *, limit: int = 50
) -> list[dict]:
    require_admin(db, org_id, actor_id)
    rows = db.execute(
        select(BillingLedger)
        .where(BillingLedger.org_id == org_id)
        .order_by(BillingLedger.created_at.desc())
        .limit(min(limit, 200))
    ).scalars().all()
    return [ledger_to_dict(r) for r in rows]


def list_user_billing_history(db: Session, user_id: uuid.UUID, *, limit: int = 50) -> list[dict]:
    rows = db.execute(
        select(BillingLedger)
        .where(BillingLedger.user_id == user_id, BillingLedger.scope == "personal")
        .order_by(BillingLedger.created_at.desc())
        .limit(min(limit, 200))
    ).scalars().all()
    return [ledger_to_dict(r) for r in rows]

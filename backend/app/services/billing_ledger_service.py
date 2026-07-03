"""计费流水 — 机构团队与个人订阅审计。"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.billing_ledger import BillingLedger
from backend.app.services import membership_service as ms
from backend.app.services.org_service import OrgAccessDeniedError, require_admin

LEDGER_CSV_HEADERS = [
    "id",
    "scope",
    "event",
    "plan_code",
    "plan_name",
    "tier",
    "tier_name",
    "seats",
    "amount_cny",
    "currency",
    "source",
    "stripe_session_id",
    "expires_at",
    "detail",
    "created_at",
]


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


def get_user_ledger_entry(db: Session, user_id: uuid.UUID, ledger_id: uuid.UUID) -> dict | None:
    row = db.execute(
        select(BillingLedger).where(
            BillingLedger.id == ledger_id,
            BillingLedger.user_id == user_id,
            BillingLedger.scope == "personal",
        )
    ).scalar_one_or_none()
    return ledger_to_dict(row) if row else None


def get_org_ledger_entry(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, ledger_id: uuid.UUID
) -> dict | None:
    require_admin(db, org_id, actor_id)
    row = db.execute(
        select(BillingLedger).where(
            BillingLedger.id == ledger_id,
            BillingLedger.org_id == org_id,
        )
    ).scalar_one_or_none()
    return ledger_to_dict(row) if row else None


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        return dt.isoformat()
    return dt.astimezone().isoformat()


def rows_to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=LEDGER_CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                **row,
                "id": str(row.get("id", "")),
                "seats": "" if row.get("seats") is None else row["seats"],
                "stripe_session_id": row.get("stripe_session_id") or "",
                "expires_at": _fmt_dt(row.get("expires_at")),
                "created_at": _fmt_dt(row.get("created_at")),
            }
        )
    return buf.getvalue()


def export_org_billing_csv(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, *, limit: int = 500
) -> str:
    rows = list_org_billing_history(db, org_id, actor_id, limit=limit)
    return rows_to_csv(rows)


def export_user_billing_csv(db: Session, user_id: uuid.UUID, *, limit: int = 500) -> str:
    rows = list_user_billing_history(db, user_id, limit=limit)
    return rows_to_csv(rows)


def _pdf_escape(text: object) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text_lines(lines: list[str]) -> bytes:
    stream_lines = ["BT", "/F1 12 Tf", "72 760 Td"]
    for idx, line in enumerate(lines):
        if idx:
            stream_lines.append("0 -22 Td")
        stream_lines.append(f"({_pdf_escape(line)}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("utf-8")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets: list[int] = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode("ascii"))
        out.write(obj)
        out.write(b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return out.getvalue()


def render_invoice_pdf(row: dict, *, billing_profile: dict | None = None) -> bytes:
    created = row.get("created_at")
    expires = row.get("expires_at")
    lines = ["QuantLab Billing Receipt"]
    if billing_profile and billing_profile.get("configured"):
        company = (billing_profile.get("company_name") or "").strip()
        tax_id = (billing_profile.get("tax_id") or "").strip()
        address = (billing_profile.get("address") or "").strip()
        if company:
            lines.append(f"Bill To: {company}")
        if tax_id:
            lines.append(f"Tax ID: {tax_id}")
        if address:
            lines.append(f"Address: {address}")
        lines.append("---")
    lines.extend(
        [
            f"Receipt ID: {row.get('id')}",
            f"Scope: {row.get('scope')}",
            f"Event: {row.get('event')}",
            f"Plan: {row.get('plan_name')} ({row.get('plan_code')})",
            f"Tier: {row.get('tier_name')}",
            f"Amount: {row.get('currency', 'CNY')} {row.get('amount_cny')}",
            f"Source: {row.get('source')}",
            f"Stripe Session: {row.get('stripe_session_id') or '-'}",
            f"Created At: {_fmt_dt(created) if isinstance(created, datetime) else created}",
            f"Expires At: {_fmt_dt(expires) if isinstance(expires, datetime) else (expires or '-')}",
            f"Detail: {row.get('detail') or '-'}",
        ]
    )
    return _pdf_text_lines(lines)

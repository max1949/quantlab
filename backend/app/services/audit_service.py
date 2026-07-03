"""审计日志写入。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.audit import AuditEvent


def log(
    db: Session,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | uuid.UUID = "",
    detail: dict | None = None,
    ip: str | None = None,
    note: str = "",
    commit: bool = True,
) -> AuditEvent:
    row = AuditEvent(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "",
        detail=detail or {},
        ip=ip,
        note=note or "",
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def list_recent(db: Session, *, limit: int = 100) -> list[AuditEvent]:
    cap = max(1, min(int(limit), 500))
    return list(
        db.execute(
            select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(cap)
        ).scalars().all()
    )

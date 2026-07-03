"""研究机构 / 团队因子库服务。"""

from __future__ import annotations

import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.audit import AuditEvent
from backend.app.models.factor import Factor
from backend.app.models.organization import (
    OrgFactorShare,
    OrgInvite,
    OrgMember,
    OrgRole,
    ResearchOrg,
)
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.services import factor_service, market_data_policy as mdp
from backend.app.services import audit_service
from engine import advanced_research as ar

_WRITE_ROLES = frozenset({OrgRole.OWNER.value, OrgRole.ADMIN.value, OrgRole.MEMBER.value})
_ADMIN_ROLES = frozenset({OrgRole.OWNER.value, OrgRole.ADMIN.value})


class OrgNotFoundError(Exception):
    pass


class OrgAccessDeniedError(Exception):
    pass


class OrgMemberNotFoundError(Exception):
    pass


class OrgInviteInvalidError(Exception):
    pass


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "org"
    return base[:48]


def _unique_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug = base
    n = 1
    while db.execute(select(ResearchOrg.id).where(ResearchOrg.slug == slug)).scalar_one_or_none():
        n += 1
        slug = f"{base}-{n}"
    return slug


def _member_row(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgMember | None:
    return db.execute(
        select(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
    ).scalar_one_or_none()


def require_member(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgMember:
    row = _member_row(db, org_id, user_id)
    if row is None:
        raise OrgAccessDeniedError(str(org_id))
    return row


def require_write_member(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgMember:
    row = require_member(db, org_id, user_id)
    if row.role not in _WRITE_ROLES:
        raise OrgAccessDeniedError("需要成员及以上权限")
    return row


def require_admin(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgMember:
    row = require_member(db, org_id, user_id)
    if row.role not in _ADMIN_ROLES:
        raise OrgAccessDeniedError("需要管理员权限")
    return row


def _org_counts(db: Session, org_id: uuid.UUID) -> tuple[int, int]:
    members = db.execute(
        select(func.count()).select_from(OrgMember).where(OrgMember.org_id == org_id)
    ).scalar_one()
    shares = db.execute(
        select(func.count()).select_from(OrgFactorShare).where(OrgFactorShare.org_id == org_id)
    ).scalar_one()
    return int(members or 0), int(shares or 0)


def _to_org_out(
    org: ResearchOrg, *, member_count: int, shared_factor_count: int, my_role: str | None
) -> dict:
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "owner_id": org.owner_id,
        "created_at": org.created_at,
        "member_count": member_count,
        "shared_factor_count": shared_factor_count,
        "my_role": my_role,
    }


def create_org(db: Session, owner: User, name: str) -> dict:
    org = ResearchOrg(name=name.strip(), slug=_unique_slug(db, name), owner_id=owner.id)
    db.add(org)
    db.flush()
    db.add(OrgMember(org_id=org.id, user_id=owner.id, role=OrgRole.OWNER.value))
    db.commit()
    db.refresh(org)
    return _to_org_out(org, member_count=1, shared_factor_count=0, my_role=OrgRole.OWNER.value)


def list_orgs_for_user(db: Session, user_id: uuid.UUID) -> list[dict]:
    org_ids = [
        row[0]
        for row in db.execute(select(OrgMember.org_id).where(OrgMember.user_id == user_id)).all()
    ]
    if not org_ids:
        return []
    out: list[dict] = []
    for org in db.execute(select(ResearchOrg).where(ResearchOrg.id.in_(org_ids))).scalars().all():
        mc, sc = _org_counts(db, org.id)
        role = _member_row(db, org.id, user_id)
        out.append(_to_org_out(org, member_count=mc, shared_factor_count=sc, my_role=role.role if role else None))
    out.sort(key=lambda x: x["created_at"], reverse=True)
    return out


def get_org(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    org = db.get(ResearchOrg, org_id)
    if org is None:
        raise OrgNotFoundError(str(org_id))
    member = require_member(db, org_id, user_id)
    mc, sc = _org_counts(db, org_id)
    return _to_org_out(org, member_count=mc, shared_factor_count=sc, my_role=member.role)


def add_member(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, username: str, role: str
) -> OrgMember:
    require_admin(db, org_id, actor_id)
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        raise OrgMemberNotFoundError(username)
    if _member_row(db, org_id, user.id):
        return _member_row(db, org_id, user.id)  # type: ignore[return-value]
    row = OrgMember(org_id=org_id, user_id=user.id, role=role)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_member_role(
    db: Session,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    target_user_id: uuid.UUID,
    role: str,
) -> OrgMember:
    actor = require_admin(db, org_id, actor_id)
    target = _member_row(db, org_id, target_user_id)
    if target is None:
        raise OrgMemberNotFoundError(str(target_user_id))
    if target.role == OrgRole.OWNER.value:
        raise OrgAccessDeniedError("不能修改所有者角色")
    if role == OrgRole.OWNER.value:
        raise OrgAccessDeniedError("不能设置为所有者")
    if role == OrgRole.ADMIN.value and actor.role != OrgRole.OWNER.value:
        raise OrgAccessDeniedError("仅所有者可设置管理员")
    target.role = role
    db.commit()
    db.refresh(target)
    return target


def remove_member(
    db: Session,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    target_user_id: uuid.UUID,
) -> None:
    actor = require_member(db, org_id, actor_id)
    target = _member_row(db, org_id, target_user_id)
    if target is None:
        return
    if target.role == OrgRole.OWNER.value:
        raise OrgAccessDeniedError("不能移除所有者")
    is_self = actor_id == target_user_id
    if not is_self and actor.role not in _ADMIN_ROLES:
        raise OrgAccessDeniedError("需要管理员权限")
    if (
        actor.role == OrgRole.ADMIN.value
        and target.role == OrgRole.ADMIN.value
        and not is_self
    ):
        raise OrgAccessDeniedError("管理员不能移除其他管理员")
    db.delete(target)
    db.commit()


def list_invites(db: Session, org_id: uuid.UUID, actor_id: uuid.UUID) -> list[dict]:
    require_admin(db, org_id, actor_id)
    now = datetime.now(timezone.utc)
    rows = list(
        db.execute(
            select(OrgInvite)
            .where(OrgInvite.org_id == org_id)
            .order_by(OrgInvite.created_at.desc())
        )
        .scalars()
        .all()
    )
    out: list[dict] = []
    for inv in rows:
        expires = inv.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        active = expires > now and inv.used_count < inv.max_uses
        out.append({**_invite_to_dict(db, inv), "active": active})
    return out


def revoke_invite(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, invite_id: uuid.UUID
) -> None:
    require_admin(db, org_id, actor_id)
    invite = db.get(OrgInvite, invite_id)
    if invite is None or invite.org_id != org_id:
        return
    db.delete(invite)
    db.commit()


def _event_belongs_to_org(event: AuditEvent, org_id: str) -> bool:
    if event.resource_type == "org" and event.resource_id == org_id:
        return True
    detail = event.detail or {}
    return str(detail.get("org_id", "")) == org_id


def org_activity(db: Session, org_id: uuid.UUID, user_id: uuid.UUID, *, limit: int = 50) -> list[dict]:
    require_member(db, org_id, user_id)
    oid = str(org_id)
    rows = audit_service.list_recent(db, limit=300, action_prefix="org")
    filtered = [r for r in rows if _event_belongs_to_org(r, oid)][: max(1, min(limit, 100))]
    return [
        {
            "id": str(r.id),
            "action": r.action,
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "detail": r.detail,
            "created_at": r.created_at.isoformat(),
        }
        for r in filtered
    ]


def _invite_to_dict(db: Session, invite: OrgInvite) -> dict:
    org = db.get(ResearchOrg, invite.org_id)
    if org is None:
        raise OrgInviteInvalidError("机构不存在")
    return {
        "id": invite.id,
        "org_id": invite.org_id,
        "org_name": org.name,
        "token": invite.token,
        "role": invite.role,
        "max_uses": invite.max_uses,
        "used_count": invite.used_count,
        "expires_at": invite.expires_at,
        "created_at": invite.created_at,
        "invite_path": f"/app/org-invite/{invite.token}",
    }


def create_invite(
    db: Session,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    *,
    role: str = OrgRole.MEMBER.value,
    expires_in_days: int = 7,
    max_uses: int = 1,
) -> dict:
    require_admin(db, org_id, actor_id)
    token = secrets.token_urlsafe(32)
    invite = OrgInvite(
        org_id=org_id,
        token=token,
        role=role,
        created_by=actor_id,
        max_uses=max(1, int(max_uses)),
        used_count=0,
        expires_at=datetime.now(timezone.utc) + timedelta(days=max(1, int(expires_in_days))),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _invite_to_dict(db, invite)


def _load_valid_invite(db: Session, token: str) -> OrgInvite:
    invite = db.execute(select(OrgInvite).where(OrgInvite.token == token)).scalar_one_or_none()
    if invite is None:
        raise OrgInviteInvalidError("邀请链接不存在")
    now = datetime.now(timezone.utc)
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise OrgInviteInvalidError("邀请链接已过期")
    if invite.used_count >= invite.max_uses:
        raise OrgInviteInvalidError("邀请次数已用尽")
    if db.get(ResearchOrg, invite.org_id) is None:
        raise OrgInviteInvalidError("机构不存在")
    return invite


def preview_invite(db: Session, token: str, user_id: uuid.UUID) -> dict:
    invite = _load_valid_invite(db, token)
    org = db.get(ResearchOrg, invite.org_id)
    return {
        "org_id": invite.org_id,
        "org_name": org.name if org else "",
        "role": invite.role,
        "expires_at": invite.expires_at,
        "used_count": invite.used_count,
        "max_uses": invite.max_uses,
        "already_member": _member_row(db, invite.org_id, user_id) is not None,
    }


def accept_invite(db: Session, token: str, user_id: uuid.UUID) -> dict:
    invite = _load_valid_invite(db, token)
    existing = _member_row(db, invite.org_id, user_id)
    if existing is None:
        db.add(OrgMember(org_id=invite.org_id, user_id=user_id, role=invite.role))
        invite.used_count += 1
        db.commit()
    else:
        db.commit()
    return get_org(db, invite.org_id, user_id)


def list_members(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> list[dict]:
    require_member(db, org_id, user_id)
    rows = db.execute(
        select(OrgMember, User)
        .join(User, User.id == OrgMember.user_id)
        .where(OrgMember.org_id == org_id)
        .order_by(OrgMember.created_at)
    ).all()
    return [
        {
            "user_id": m.user_id,
            "username": u.username,
            "role": m.role,
            "joined_at": m.created_at,
        }
        for m, u in rows
    ]


def share_factor(
    db: Session,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    factor_id: uuid.UUID,
    *,
    note: str = "",
) -> OrgFactorShare:
    require_write_member(db, org_id, user_id)
    factor = db.get(Factor, factor_id)
    if factor is None or factor.owner_id != user_id:
        raise OrgAccessDeniedError("只能共享自己的因子")
    existing = db.execute(
        select(OrgFactorShare).where(
            OrgFactorShare.org_id == org_id, OrgFactorShare.factor_id == factor_id
        )
    ).scalar_one_or_none()
    if existing:
        existing.note = note or existing.note
        db.commit()
        db.refresh(existing)
        return existing
    row = OrgFactorShare(org_id=org_id, factor_id=factor_id, shared_by=user_id, note=note or "")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def unshare_factor(db: Session, org_id: uuid.UUID, user_id: uuid.UUID, factor_id: uuid.UUID) -> None:
    member = require_write_member(db, org_id, user_id)
    share = db.execute(
        select(OrgFactorShare).where(
            OrgFactorShare.org_id == org_id, OrgFactorShare.factor_id == factor_id
        )
    ).scalar_one_or_none()
    if share is None:
        return
    factor = db.get(Factor, factor_id)
    if factor is None:
        db.delete(share)
        db.commit()
        return
    if factor.owner_id != user_id and member.role not in _ADMIN_ROLES:
        raise OrgAccessDeniedError("仅因子所有者或管理员可取消共享")
    db.delete(share)
    db.commit()


def list_shared_factors(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> list[dict]:
    require_member(db, org_id, user_id)
    rows = db.execute(
        select(OrgFactorShare, Factor, User)
        .join(Factor, Factor.id == OrgFactorShare.factor_id)
        .join(User, User.id == Factor.owner_id)
        .where(OrgFactorShare.org_id == org_id)
        .order_by(OrgFactorShare.created_at.desc())
    ).all()
    return [
        {
            "factor_id": f.id,
            "factor_name": f.name,
            "owner_username": u.username,
            "kind": f.kind,
            "note": s.note,
            "shared_at": s.created_at,
        }
        for s, f, u in rows
    ]


def _latest_backtest(db: Session, factor_id: uuid.UUID) -> Backtest | None:
    return db.execute(
        select(Backtest)
        .where(Backtest.factor_id == factor_id, Backtest.status == BacktestStatus.SUCCESS.value)
        .order_by(Backtest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_validation(db: Session, factor_id: uuid.UUID) -> Validation | None:
    return db.execute(
        select(Validation)
        .where(Validation.factor_id == factor_id, Validation.status == ValidationStatus.SUCCESS.value)
        .order_by(Validation.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def org_catalog(
    db: Session,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    symbol: str | None = None,
    timeframe: str = "1d",
) -> dict:
    """团队因子资产库 — 跨成员绩效元数据 + 机构级冗余扫描。"""
    require_member(db, org_id, user_id)
    shares = list(
        db.execute(select(OrgFactorShare).where(OrgFactorShare.org_id == org_id)).scalars().all()
    )
    factor_ids = [s.factor_id for s in shares]
    if not factor_ids:
        return {
            "org_id": str(org_id),
            "symbol": (symbol or "").upper() or None,
            "timeframe": timeframe,
            "factors": [],
            "redundancy_pairs": [],
            "high_overlap_count": 0,
        }

    factors = list(db.execute(select(Factor).where(Factor.id.in_(factor_ids))).scalars().all())
    share_by_factor = {s.factor_id: s for s in shares}
    viewer = db.get(User, user_id)

    ohlcv = None
    sym = (symbol or "").upper()
    if sym and viewer is not None:
        try:
            ohlcv = mdp.load_for_user(db, viewer, sym, timeframe)
        except mdp.MarketDataAccessError:
            ohlcv = None

    entries: list[dict] = []
    series_map: dict[uuid.UUID, pd.Series] = {}
    for f in factors:
        bt = _latest_backtest(db, f.id)
        val = _latest_validation(db, f.id)
        owner = db.get(User, f.owner_id)
        oos_sharpe = None
        robustness = None
        if val and val.oos:
            oos_sharpe = (val.oos.get("out_of_sample") or {}).get("sharpe")
        if val and val.robustness:
            robustness = val.robustness.get("score")
        if ohlcv is not None and not ohlcv.empty:
            try:
                s = factor_service.compute_factor_series(db, f.owner_id, f, ohlcv)
                series_map[f.id] = s
            except factor_service.FactorValidationError:
                pass
        sh = share_by_factor.get(f.id)
        entries.append(
            {
                "factor_id": str(f.id),
                "name": f.name,
                "kind": f.kind,
                "owner_username": owner.username if owner else None,
                "template_type": f.template_type,
                "version": f.version,
                "sharpe": (bt.metrics or {}).get("sharpe") if bt else None,
                "oos_sharpe": oos_sharpe,
                "robustness_score": robustness,
                "symbol": bt.symbol if bt else sym or None,
                "timeframe": timeframe,
                "share_note": sh.note if sh else "",
            }
        )

    redundancy: list[dict] = []
    ids = list(series_map.keys())
    for i, a_id in enumerate(ids):
        for b_id in ids[i + 1 :]:
            fa = next(x for x in factors if x.id == a_id)
            fb = next(x for x in factors if x.id == b_id)
            orth = ar.orthogonalize(series_map[a_id], {fb.name: series_map[b_id]})
            r2 = orth.get("r_squared")
            if r2 is None:
                continue
            redundancy.append(
                {
                    "factor_a": str(a_id),
                    "factor_b": str(b_id),
                    "name_a": fa.name,
                    "name_b": fb.name,
                    "owner_a": db.get(User, fa.owner_id).username if fa.owner_id else None,
                    "owner_b": db.get(User, fb.owner_id).username if fb.owner_id else None,
                    "r_squared": r2,
                    "verdict": orth.get("verdict"),
                    "high_overlap": r2 >= 0.35,
                }
            )
    redundancy.sort(key=lambda x: -(x.get("r_squared") or 0))

    return {
        "org_id": str(org_id),
        "symbol": sym or None,
        "timeframe": timeframe,
        "factors": entries,
        "redundancy_pairs": redundancy[:30],
        "high_overlap_count": sum(1 for r in redundancy if r.get("high_overlap")),
    }

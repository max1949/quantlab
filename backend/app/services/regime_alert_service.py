"""工作台主动提醒 — 制度切换、弱适配、Paper 衰减。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.execution import PaperOrder
from backend.app.models.factor import Factor
from backend.app.models.growth import AttentionAlertDismissal
from backend.app.models.project import ResearchProject
from backend.app.models.user import User
from backend.app.services import market_data_policy as mdp
from backend.app.services import paper_tracking_service as pts
from backend.app.services.research_quality_service import _representative_factor_id

_SEVERITY_ORDER = {"info": 0, "watch": 1, "alert": 2}
_MAX_ALERTS = 5
_WEAK_FIT_THRESHOLD = 55


def make_alert_key(
    kind: str,
    *,
    project_id: str | None = None,
    factor_id: str | None = None,
    symbol: str | None = None,
) -> str:
    if kind == "paper_decay" and factor_id:
        return f"paper_decay:{factor_id}"
    if project_id:
        return f"{kind}:{project_id}"
    return f"{kind}:{symbol or 'general'}"


def dismiss_attention_alert(db: Session, user_id: uuid.UUID, alert_key: str) -> dict:
    """用户忽略提醒 — 冷却期内不再展示。"""
    key = alert_key.strip()
    if not key or len(key) > 128:
        raise ValueError("无效的提醒标识")
    now = datetime.now(timezone.utc)
    row = db.execute(
        select(AttentionAlertDismissal).where(
            AttentionAlertDismissal.user_id == user_id,
            AttentionAlertDismissal.alert_key == key,
        )
    ).scalar_one_or_none()
    if row is None:
        row = AttentionAlertDismissal(user_id=user_id, alert_key=key, dismissed_at=now)
        db.add(row)
    else:
        row.dismissed_at = now
    db.commit()
    days = get_settings().attention_alert_cooldown_days
    return {"alert_key": key, "cooldown_days": days, "dismissed_at": now.isoformat()}


def restore_attention_alert(db: Session, user_id: uuid.UUID, alert_key: str) -> dict:
    """提前恢复被忽略的提醒。"""
    key = alert_key.strip()
    if not key or len(key) > 128:
        raise ValueError("无效的提醒标识")
    row = db.execute(
        select(AttentionAlertDismissal).where(
            AttentionAlertDismissal.user_id == user_id,
            AttentionAlertDismissal.alert_key == key,
        )
    ).scalar_one_or_none()
    if row is None:
        raise ValueError("未找到该忽略记录")
    db.delete(row)
    db.commit()
    return {"alert_key": key, "restored": True}


def _cooldown_days() -> int:
    return max(1, get_settings().attention_alert_cooldown_days)


def _parse_alert_key(alert_key: str) -> tuple[str, str | None]:
    if ":" not in alert_key:
        return alert_key, None
    kind, ref = alert_key.split(":", 1)
    return kind, ref or None


def _ref_label(db: Session, user_id: uuid.UUID, alert_key: str) -> str | None:
    kind, ref = _parse_alert_key(alert_key)
    if not ref:
        return None
    if kind == "paper_decay":
        try:
            factor = db.get(Factor, uuid.UUID(ref))
            if factor and factor.owner_id == user_id:
                return factor.name
        except ValueError:
            return ref
        return ref
    try:
        proj = db.get(ResearchProject, uuid.UUID(ref))
        if proj and proj.owner_id == user_id:
            return proj.title
    except ValueError:
        return ref
    return ref


def list_dismissed_history(db: Session, user: User, locale: Locale = "en") -> dict:
    """冷却期内已忽略的提醒历史。"""
    days = _cooldown_days()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = list(
        db.execute(
            select(AttentionAlertDismissal)
            .where(
                AttentionAlertDismissal.user_id == user.id,
                AttentionAlertDismissal.dismissed_at >= cutoff,
            )
            .order_by(AttentionAlertDismissal.dismissed_at.desc())
        )
        .scalars()
        .all()
    )
    kind_labels = i18n.ATTENTION_HISTORY_KIND.get(locale) or i18n.ATTENTION_HISTORY_KIND["en"]
    items: list[dict] = []
    now = datetime.now(timezone.utc)
    for row in rows:
        kind, _ = _parse_alert_key(row.alert_key)
        dismissed = row.dismissed_at
        if dismissed.tzinfo is None:
            dismissed = dismissed.replace(tzinfo=timezone.utc)
        expires = dismissed + timedelta(days=days)
        delta = expires - now
        if delta.total_seconds() <= 0:
            remaining = 0
        elif delta.days == 0:
            remaining = 1
        else:
            remaining = delta.days
        items.append(
            {
                "alert_key": row.alert_key,
                "kind": kind,
                "kind_label": kind_labels.get(kind, kind),
                "ref_label": _ref_label(db, user.id, row.alert_key),
                "dismissed_at": dismissed.isoformat(),
                "expires_at": expires.isoformat(),
                "days_remaining": remaining,
            }
        )
    return {"cooldown_days": days, "items": items}


def _dismissed_keys(db: Session, user_id: uuid.UUID) -> set[str]:
    days = _cooldown_days()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(AttentionAlertDismissal.alert_key).where(
            AttentionAlertDismissal.user_id == user_id,
            AttentionAlertDismissal.dismissed_at >= cutoff,
        )
    ).scalars()
    return set(rows.all())


def list_attention_alerts(
    db: Session,
    user: User,
    locale: Locale = "en",
    *,
    max_projects: int = 5,
) -> list[dict]:
    """扫描用户近期项目与 Paper 因子, 返回需主动关注的提醒列表。"""
    labels = i18n.ATTENTION_ALERT.get(locale) or i18n.ATTENTION_ALERT["en"]
    regime_labels = i18n.REGIME_LABEL.get(locale) or i18n.REGIME_LABEL["en"]
    verdict_labels = i18n.FIT_VERDICT_LABEL.get(locale) or i18n.FIT_VERDICT_LABEL["en"]
    alerts: list[dict] = []
    seen: set[str] = set()
    dismissed = _dismissed_keys(db, user.id)

    projects = list(
        db.execute(
            select(ResearchProject)
            .where(ResearchProject.owner_id == user.id)
            .order_by(ResearchProject.updated_at.desc())
            .limit(max_projects)
        )
        .scalars()
        .all()
    )

    for project in projects:
        factor_id = _representative_factor_id(db, project.id)
        if factor_id is None:
            continue
        factor = db.get(Factor, factor_id)
        if factor is None:
            continue
        symbol = project.symbol or "RB"
        pid = str(project.id)

        shift = _detect_shift_for_symbol(db, user, symbol)
        if shift and shift.get("shifted"):
            akey = make_alert_key("regime_shift", project_id=pid)
            if akey in dismissed or akey in seen:
                pass
            else:
                seen.add(akey)
                from_l = regime_labels.get(shift["from_regime"], shift.get("from_label", ""))
                to_l = regime_labels.get(shift["to_regime"], shift.get("to_label", ""))
                alerts.append(
                    _alert(
                        kind="regime_shift",
                        alert_key=akey,
                        title=labels["regime_shift_title"].format(symbol=symbol),
                        message=labels["regime_shift_msg"].format(
                            from_label=from_l,
                            to_label=to_l,
                            project_title=project.title,
                        ),
                        project_id=pid,
                        symbol=symbol,
                        action="revalidate",
                        cta_path=f"/projects/{pid}",
                        severity="watch",
                    )
                )

        regime = _regime_fit(db, user, symbol, factor)
        fit_score = regime.get("fit_score") if regime else None
        if fit_score is not None and fit_score < _WEAK_FIT_THRESHOLD:
            akey = make_alert_key("weak_regime_fit", project_id=pid)
            if akey not in dismissed and akey not in seen:
                seen.add(akey)
                verdict = verdict_labels.get(
                    regime.get("fit_verdict", ""), regime.get("fit_verdict", "")
                )
                alerts.append(
                    _alert(
                        kind="weak_regime_fit",
                        alert_key=akey,
                        title=labels["weak_fit_title"].format(symbol=symbol),
                        message=labels["weak_fit_msg"].format(
                            project_title=project.title,
                            verdict=verdict,
                            score=fit_score,
                        ),
                        project_id=pid,
                        symbol=symbol,
                        action="templates",
                        cta_path=f"/templates?symbol={symbol}",
                        severity="info",
                    )
                )

    paper_factor_ids = list(
        db.execute(
            select(PaperOrder.factor_id)
            .where(
                PaperOrder.user_id == user.id,
                PaperOrder.factor_id.isnot(None),
            )
            .distinct()
            .limit(3)
        )
        .scalars()
        .all()
    )

    for fid in paper_factor_ids:
        if fid is None:
            continue
        akey = make_alert_key("paper_decay", factor_id=str(fid))
        if akey in dismissed or akey in seen:
            continue
        decay = pts.assess_factor_decay(db, fid, user.id)
        status = decay.get("status", "ok")
        if status not in ("watch", "alert"):
            continue
        factor = db.get(Factor, fid)
        project_id = str(factor.project_id) if factor and factor.project_id else None
        symbol = None
        if factor and factor.project_id:
            proj = db.get(ResearchProject, factor.project_id)
            symbol = proj.symbol if proj else None
        seen.add(akey)
        reason = (decay.get("reasons") or [""])[0]
        title_key = "paper_decay_alert_title" if status == "alert" else "paper_decay_watch_title"
        alerts.append(
            _alert(
                kind="paper_decay",
                alert_key=akey,
                title=labels[title_key].format(
                    factor_name=factor.name if factor else labels["paper_factor_fallback"]
                ),
                message=reason or labels["paper_decay_msg"],
                project_id=project_id,
                symbol=symbol,
                action="revalidate",
                cta_path=f"/projects/{project_id}" if project_id else "/projects",
                severity=status,
            )
        )

    alerts.sort(key=lambda a: (-_SEVERITY_ORDER.get(a["severity"], 0), a["kind"]))
    return alerts[:_MAX_ALERTS]


def _alert(
    *,
    kind: str,
    alert_key: str,
    title: str,
    message: str,
    project_id: str | None,
    symbol: str | None,
    action: str,
    cta_path: str,
    severity: str,
) -> dict:
    return {
        "kind": kind,
        "alert_key": alert_key,
        "title": title,
        "message": message,
        "project_id": project_id,
        "symbol": symbol,
        "action": action,
        "cta_path": cta_path,
        "severity": severity,
    }


def _detect_shift_for_symbol(db: Session, user: User, symbol: str) -> dict | None:
    try:
        from engine.regime import detect_regime_shift

        df = mdp.load_for_user(db, user, symbol, "1d")
        return detect_regime_shift(df)
    except Exception:  # noqa: BLE001 — 提醒为可选增强
        return None


def _regime_fit(db: Session, user: User, symbol: str, factor: Factor) -> dict | None:
    from backend.app.services import regime_advisory

    return regime_advisory.market_regime_for_symbol(db, user, symbol, "1d", factor=factor)


def project_attention_context(
    db: Session,
    user: User,
    project: ResearchProject,
    *,
    factor_id: uuid.UUID | None = None,
    regime: dict | None = None,
    paper_decay: dict | None = None,
) -> dict:
    """单项目关注上下文 — 供联合教练与导师联动。"""
    symbol = project.symbol or "RB"
    fid = factor_id or _representative_factor_id(db, project.id)
    factor = db.get(Factor, fid) if fid else None

    shift_raw = _detect_shift_for_symbol(db, user, symbol)
    regime_shift = shift_raw if shift_raw and shift_raw.get("shifted") else None

    if regime is None and factor:
        regime = _regime_fit(db, user, symbol, factor)
    fit_score = regime.get("fit_score") if regime else None
    weak_regime_fit = fit_score is not None and fit_score < _WEAK_FIT_THRESHOLD

    decay_active = bool(paper_decay and paper_decay.get("status") in ("watch", "alert"))

    return {
        "regime_shift": regime_shift,
        "weak_regime_fit": weak_regime_fit,
        "fit_score": fit_score,
        "fit_verdict": regime.get("fit_verdict") if regime else None,
        "paper_decay": paper_decay if decay_active else None,
        "symbol": symbol,
    }

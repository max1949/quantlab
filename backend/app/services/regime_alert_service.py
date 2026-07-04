"""工作台主动提醒 — 制度切换、弱适配、Paper 衰减。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.execution import PaperOrder
from backend.app.models.factor import Factor
from backend.app.models.project import ResearchProject
from backend.app.models.user import User
from backend.app.services import market_data_policy as mdp
from backend.app.services import paper_tracking_service as pts
from backend.app.services.research_quality_service import _representative_factor_id

_SEVERITY_ORDER = {"info": 0, "watch": 1, "alert": 2}
_MAX_ALERTS = 5
_WEAK_FIT_THRESHOLD = 55


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
    seen: set[tuple[str, str | None]] = set()

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
            key = ("regime_shift", pid)
            if key not in seen:
                seen.add(key)
                from_l = regime_labels.get(shift["from_regime"], shift.get("from_label", ""))
                to_l = regime_labels.get(shift["to_regime"], shift.get("to_label", ""))
                alerts.append(
                    _alert(
                        kind="regime_shift",
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
            key = ("weak_regime_fit", pid)
            if key not in seen:
                seen.add(key)
                verdict = verdict_labels.get(
                    regime.get("fit_verdict", ""), regime.get("fit_verdict", "")
                )
                alerts.append(
                    _alert(
                        kind="weak_regime_fit",
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
        key = ("paper_decay", str(fid))
        if key in seen:
            continue
        seen.add(key)
        reason = (decay.get("reasons") or [""])[0]
        title_key = "paper_decay_alert_title" if status == "alert" else "paper_decay_watch_title"
        alerts.append(
            _alert(
                kind="paper_decay",
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

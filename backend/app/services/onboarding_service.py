"""分流 + onboarding (Sprint 9A)。

按"分流身份 + 当前研究进度"算出"下一步该做什么", 给小白明确指引。
该 next_step 同时被 onboarding/next 与 AI 研究导师 (/ai/mentor/next) 复用。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User, UserType
from backend.app.models.validation import Validation, ValidationStatus

TYPE_DEFAULT_TEMPLATE = {
    UserType.NEWBIE.value: "gold-trend",
    UserType.PYTHON.value: "commodity-momentum",
    UserType.TRADER.value: "vol-regime",
}


def choose_type(db: Session, user: User, user_type: str) -> User:
    if user_type not in {t.value for t in UserType}:
        raise ValueError("未知用户类型")
    user.user_type = user_type
    user.onboarding_done = True
    db.commit()
    db.refresh(user)
    return user


def _count(db: Session, stmt) -> int:
    return int(db.execute(stmt).scalar_one() or 0)


def _active_project_id(db: Session, user: User):
    """用户最近更新的研究项目 — 用于「下一步」深链到具体项目页。"""
    return db.execute(
        select(ResearchProject.id)
        .where(ResearchProject.owner_id == user.id)
        .order_by(ResearchProject.updated_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _stage(db: Session, user: User) -> str:
    uid = user.id
    projects = _count(db, select(func.count(ResearchProject.id)).where(ResearchProject.owner_id == uid))
    if projects == 0:
        return "create_project"
    factors = _count(db, select(func.count(Factor.id)).where(Factor.owner_id == uid))
    if factors == 0:
        return "create_factor"
    bt = _count(
        db,
        select(func.count(Backtest.id)).where(
            Backtest.owner_id == uid, Backtest.status == BacktestStatus.SUCCESS.value
        ),
    )
    if bt == 0:
        return "run_backtest"
    val = _count(
        db,
        select(func.count(Validation.id)).where(
            Validation.owner_id == uid, Validation.status == ValidationStatus.SUCCESS.value
        ),
    )
    if val == 0:
        return "run_validation"
    reports = _count(db, select(func.count(ResearchReport.id)).where(ResearchReport.owner_id == uid))
    if reports == 0:
        return "generate_report"
    published = _count(
        db,
        select(func.count(ResearchProject.id)).where(
            ResearchProject.owner_id == uid, ResearchProject.status == ProjectStatus.PUBLISHED.value
        ),
    )
    if published == 0:
        return "publish_share"
    return "keep_going"


def next_step(db: Session, user: User, locale: Locale = "en") -> dict:
    """返回个性化下一步 (身份 + 进度)。"""
    stage = _stage(db, user)
    detail = i18n.STEP_DETAIL[stage][locale]
    user_type = user.user_type
    active_id = _active_project_id(db, user)
    project_stages = {
        "create_factor",
        "run_backtest",
        "run_validation",
        "generate_report",
        "publish_share",
    }
    if active_id and stage in project_stages:
        cta_path = f"/projects/{active_id}"
    else:
        cta_path = {
            "create_project": "/templates",
            "create_factor": "/projects",
            "run_backtest": "/projects",
            "run_validation": "/projects",
            "generate_report": "/dashboard",
            "publish_share": "/dashboard",
            "keep_going": "/feed",
        }[stage]
    out = {
        "user_type": user_type,
        "user_type_label": i18n.USER_TYPE_LABEL.get(user_type, {}).get(locale, user_type),
        "intro": i18n.TYPE_INTRO.get(user_type, {}).get(locale, ""),
        "stage": stage,
        "title": detail["title"],
        "action": detail["action"],
        "cta_path": cta_path,
        "active_project_id": active_id,
    }
    if stage == "create_project":
        out["recommended_template"] = TYPE_DEFAULT_TEMPLATE.get(user_type, "gold-trend")
    return out


JOURNEY_STEP_KEYS = (
    "template",
    "factor",
    "backtest",
    "validation",
    "report",
    "publish",
    "share",
)


def research_journey(db: Session, user: User, locale: Locale = "en") -> dict:
    """七步研究闭环进度 (工作台进度环)。"""
    from backend.app.models.growth import ResearchShare

    uid = user.id
    flags = {
        "template": _count(db, select(func.count(ResearchProject.id)).where(ResearchProject.owner_id == uid)) > 0,
        "factor": _count(db, select(func.count(Factor.id)).where(Factor.owner_id == uid)) > 0,
        "backtest": _count(
            db,
            select(func.count(Backtest.id)).where(
                Backtest.owner_id == uid, Backtest.status == BacktestStatus.SUCCESS.value
            ),
        )
        > 0,
        "validation": _count(
            db,
            select(func.count(Validation.id)).where(
                Validation.owner_id == uid, Validation.status == ValidationStatus.SUCCESS.value
            ),
        )
        > 0,
        "report": _count(db, select(func.count(ResearchReport.id)).where(ResearchReport.owner_id == uid)) > 0,
        "publish": _count(
            db,
            select(func.count(ResearchProject.id)).where(
                ResearchProject.owner_id == uid, ResearchProject.status == ProjectStatus.PUBLISHED.value
            ),
        )
        > 0,
        "share": _count(db, select(func.count(ResearchShare.id)).where(ResearchShare.owner_id == uid)) > 0,
    }
    labels = i18n.JOURNEY_STEPS.get(locale) or i18n.JOURNEY_STEPS["en"]
    steps = [{"key": k, "label": labels[k], "done": flags[k]} for k in JOURNEY_STEP_KEYS]
    done_count = sum(1 for s in steps if s["done"])
    return {
        "done_count": done_count,
        "total": len(steps),
        "steps": steps,
        "active_project_id": _active_project_id(db, user),
    }

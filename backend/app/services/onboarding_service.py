"""分流 + onboarding (Sprint 9A)。

按"分流身份 + 当前研究进度"算出"下一步该做什么", 给小白明确指引。
该 next_step 同时被 onboarding/next 与 AI 研究导师 (/ai/mentor/next) 复用。
"""

from __future__ import annotations

import uuid

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


def _latest_report_id(db: Session, user: User) -> uuid.UUID | None:
    return db.execute(
        select(ResearchReport.id)
        .where(ResearchReport.owner_id == user.id)
        .order_by(ResearchReport.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _journey_flags(db: Session, user: User) -> dict[str, bool]:
    from backend.app.models.growth import ResearchShare

    uid = user.id
    return {
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


def _mastery_path_phase_rows(
    locale: Locale,
    flags: dict[str, bool],
    *,
    mastery_goal: dict,
    active_project_id: uuid.UUID | None,
) -> list[dict]:
    labels = i18n.MASTERY_OVERVIEW.get(locale) or i18n.MASTERY_OVERVIEW["en"]
    phase_keys = ("incubate", "report", "paper", "masters", "reputation")
    incubate_done = bool(flags.get("backtest") and flags.get("validation"))
    report_done = bool(flags.get("report"))
    paper_active = int(mastery_goal.get("paper_tracking_count") or 0) > 0
    paper_graduated = int(mastery_goal.get("paper_graduated_count") or 0) > 0
    reputation_done = bool(flags.get("share") or flags.get("publish"))

    done_map = {
        "incubate": incubate_done,
        "report": report_done,
        "paper": paper_active,
        "masters": paper_graduated,
        "reputation": reputation_done,
    }
    project_path = f"/projects/{active_project_id}" if active_project_id else "/projects"
    cta_map = {
        "incubate": (project_path if active_project_id else "/templates", "run_validation" if active_project_id else "create_project"),
        "report": (project_path, "generate_report"),
        "paper": (project_path, "run_paper"),
        "masters": ("/leaderboards/paper_mastery", "view_board"),
        "reputation": (project_path if active_project_id else "/feed", "publish_share"),
    }
    return [
        {
            "key": key,
            "label": labels[f"phase_{key}"],
            "hint": labels[f"phase_{key}_hint"],
            "done": done_map[key],
            "cta_path": cta_map[key][0],
            "cta_action": cta_map[key][1],
        }
        for key in phase_keys
    ]


def mastery_path_snapshot_for_user(
    db: Session,
    user: User,
    locale: Locale,
    *,
    flags: dict[str, bool] | None = None,
    mastery_goal: dict | None = None,
    active_project_id: uuid.UUID | None = None,
) -> dict:
    """五阶段大师路径快照 — 用于 Feed / 分享卡片展示。"""
    flags = flags if flags is not None else _journey_flags(db, user)
    if mastery_goal is None:
        mastery_goal = _mastery_goal_payload(db, user, locale)
    if active_project_id is None:
        active_project_id = _active_project_id(db, user)
    phases = _mastery_path_phase_rows(
        locale, flags, mastery_goal=mastery_goal, active_project_id=active_project_id
    )
    done_count = sum(1 for p in phases if p["done"])
    return {
        "done_count": done_count,
        "total": len(phases),
        "phases": [{"key": p["key"], "label": p["label"], "done": p["done"]} for p in phases],
    }


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
    active_id = _active_project_id(db, user)
    if active_id:
        from backend.app.services import research_quality_service as rqs

        q = rqs.project_quality_payload(db, active_id)
        if q.get("paper_ready") and q.get("factor_id"):
            from backend.app.models.execution import PaperOrder

            fid = uuid.UUID(q["factor_id"])
            has_po = db.execute(
                select(PaperOrder.id).where(
                    PaperOrder.user_id == uid, PaperOrder.factor_id == fid
                ).limit(1)
            ).first()
            if not has_po:
                return "run_paper"
            decay = q.get("paper_decay") or {}
            if decay.get("status") in ("watch", "alert"):
                return "revalidate_decay"
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
        "run_paper",
        "revalidate_decay",
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
            "run_paper": "/projects",
            "revalidate_decay": "/projects",
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
        default_tpl = TYPE_DEFAULT_TEMPLATE.get(user_type, "gold-trend")
        out["recommended_template"] = default_tpl
        from backend.app.services import membership_service as ms, template_service

        tier = ms.current_tier(db, user)
        regime_symbol = {"trader": "IF", "python": "RB", "newbie": "AU"}.get(user_type, "RB")
        picks_data = template_service.regime_template_picks(db, user, tier, locale, symbol=regime_symbol)
        top = picks_data["picks"][0] if picks_data.get("picks") else None
        if top:
            out["recommended_template"] = top["code"]
            out["regime_pick"] = {
                "symbol": picks_data["symbol"],
                "regime": picks_data.get("regime"),
                "regime_label": picks_data.get("regime_label"),
                "coach_hint": picks_data.get("coach_hint", ""),
                "template_code": top["code"],
                "template_title": top["title"],
                "fit_score": top["fit_score"],
                "fit_verdict": top["fit_verdict"],
            }
            if picks_data.get("regime_label"):
                fmt = i18n.REGIME_NEXT_ACTION.get(locale) or i18n.REGIME_NEXT_ACTION["en"]
                out["action"] = detail["action"] + fmt.format(
                    regime=picks_data["regime_label"],
                    title=top["title"],
                    verdict=top["fit_verdict"],
                    score=top["fit_score"],
                )
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


def quickstart_guide_payload(
    locale: Locale,
    flags: dict[str, bool],
    *,
    active_project_id: uuid.UUID | None,
    recommended_template: str | None = None,
) -> dict | None:
    """新手 3 步快速上手 — 首份报告前展示。"""
    if flags.get("report"):
        return None

    labels = i18n.QUICKSTART_GUIDE.get(locale) or i18n.QUICKSTART_GUIDE["en"]
    project_path = f"/projects/{active_project_id}" if active_project_id else "/projects"
    template_path = (
        f"/templates?focus={recommended_template}" if recommended_template else "/templates"
    )

    steps = [
        {
            "key": "start",
            "done": bool(flags.get("template") and flags.get("factor")),
            "label": labels["step1_label"],
            "hint": labels["step1_hint"],
            "cta_path": template_path,
            "cta_action": "create_project",
        },
        {
            "key": "validate",
            "done": bool(flags.get("backtest") and flags.get("validation")),
            "label": labels["step2_label"],
            "hint": labels["step2_hint"],
            "cta_path": project_path,
            "cta_action": "run_validation",
        },
        {
            "key": "report",
            "done": bool(flags.get("report")),
            "label": labels["step3_label"],
            "hint": labels["step3_hint"],
            "cta_path": project_path,
            "cta_action": "generate_report",
        },
    ]
    current_index = next((i for i, s in enumerate(steps) if not s["done"]), len(steps) - 1)
    progress = sum(1 for s in steps if s["done"])

    return {
        "title": labels["title"],
        "subtitle": labels["subtitle"],
        "current_badge": labels["current_badge"],
        "steps": steps,
        "current_index": current_index,
        "progress": progress,
        "total": len(steps),
    }


def first_project_coaching_payload(
    db: Session,
    user: User,
    locale: Locale,
    flags: dict[str, bool],
    *,
    active_project_id: uuid.UUID | None,
) -> dict | None:
    """模板开局后 — 引导跑第一次回测。"""
    if not flags.get("template") or not flags.get("factor"):
        return None
    if flags.get("backtest"):
        return None
    if not active_project_id:
        return None

    project = db.get(ResearchProject, active_project_id)
    if project is None or project.owner_id != user.id:
        return None

    factor = db.execute(
        select(Factor)
        .where(Factor.project_id == active_project_id, Factor.owner_id == user.id)
        .order_by(Factor.created_at.asc())
        .limit(1)
    ).scalar_one_or_none()
    if factor is None:
        return None

    labels = i18n.FIRST_PROJECT_COACH.get(locale) or i18n.FIRST_PROJECT_COACH["en"]
    project_path = f"/projects/{active_project_id}"
    return {
        "badge": labels["badge"],
        "celebrate": labels["celebrate"],
        "message": labels["message"],
        "unlock_features": labels["unlock_features"],
        "cta_action": "run_backtest",
        "cta_path": project_path,
        "active_project_id": active_project_id,
        "project_title": project.title,
        "factor_name": factor.name,
    }


def first_report_coaching_payload(
    db: Session,
    user: User,
    locale: Locale,
    flags: dict[str, bool],
    *,
    mastery_goal: dict,
    active_project_id: uuid.UUID | None,
) -> dict | None:
    """首份报告毕业庆祝 — 引导进入 Paper 或发布分享闭环。"""
    if not flags.get("report"):
        return None

    from backend.app.models.execution import PaperOrder

    uid = user.id
    paper_orders = _count(
        db,
        select(func.count(PaperOrder.id)).where(PaperOrder.user_id == uid),
    )
    if paper_orders > 0:
        return None

    labels = i18n.FIRST_REPORT_COACH.get(locale) or i18n.FIRST_REPORT_COACH["en"]
    project_path = f"/projects/{active_project_id}" if active_project_id else "/projects"
    paper_ready = bool(mastery_goal.get("paper_ready"))
    publish_ready = bool(mastery_goal.get("publish_ready"))

    guide_steps: list[dict] = []
    paper_guide_title = None
    if paper_ready:
        reason = "paper_ready"
        message = labels["paper_ready"]
        unlock = labels["unlock_paper"]
        cta_action = "run_paper"
        cta_path = project_path
        paper_guide_title = labels["paper_guide_title"]
        guide_steps = [
            {
                "step": 1,
                "label": labels["paper_step1_label"],
                "hint": labels["paper_step1_hint"],
                "cta_path": project_path,
                "cta_action": "run_paper",
            },
            {
                "step": 2,
                "label": labels["paper_step2_label"],
                "hint": labels["paper_step2_hint"],
                "cta_path": project_path,
                "cta_action": "run_paper",
            },
            {
                "step": 3,
                "label": labels["paper_step3_label"],
                "hint": labels["paper_step3_hint"],
                "cta_path": "/leaderboards/paper_mastery",
                "cta_action": "keep_going",
            },
        ]
    elif publish_ready:
        reason = "publish_share"
        message = labels["publish_next"]
        unlock = labels["unlock_share"]
        cta_action = "publish_share"
        cta_path = project_path
    else:
        reason = "continue_mastery"
        message = labels["continue_mastery"]
        unlock = labels["unlock_paper"]
        cta_action = "run_validation"
        cta_path = project_path

    from backend.app.services import task_service

    task_service.seed_default_tasks(db)
    academy_title = None
    academy_xp = None
    academy_completed = False
    try:
        task = task_service.get_by_code(db, "first-report")
        if task:
            academy_title = task.title
            academy_xp = task.xp_reward
            completed_ids = task_service.completed_task_ids(db, user.id)
            academy_completed = task.id in completed_ids
            if not academy_completed and flags.get("report"):
                academy_completed = True
    except task_service.TaskNotFoundError:
        pass

    challenge_milestone_done = False
    from backend.app.services import challenge_service

    ch_prog = challenge_service.progress_if_enrolled(db, user)
    if ch_prog:
        for m in ch_prog["milestones"]:
            if m["code"] == "first_report" and m["completed"]:
                challenge_milestone_done = True
                break

    return {
        "reason": reason,
        "badge": labels["badge"],
        "message": message,
        "celebrate": labels["celebrate"],
        "unlock_features": unlock,
        "cta_action": cta_action,
        "cta_path": cta_path,
        "active_project_id": active_project_id,
        "paper_ready": paper_ready,
        "academy_title": academy_title,
        "academy_xp": academy_xp,
        "academy_completed": academy_completed,
        "challenge_milestone_done": challenge_milestone_done,
        "paper_guide_title": paper_guide_title,
        "guide_steps": guide_steps,
    }


def reputation_coaching_payload(
    db: Session,
    user: User,
    locale: Locale,
    flags: dict[str, bool],
    *,
    mastery_goal: dict,
    active_project_id: uuid.UUID | None,
) -> dict | None:
    """Paper 大师榜后声誉阶段 — 发布 → 分享 → 涨粉闭环。"""
    if flags.get("share"):
        return None

    graduated = int(mastery_goal.get("paper_graduated_count") or 0)
    on_board = bool(mastery_goal.get("on_leaderboard"))
    tracking = int(mastery_goal.get("paper_tracking_count") or 0)
    if not flags.get("report"):
        return None
    if graduated <= 0 and not on_board and tracking <= 0:
        return None

    labels = i18n.REPUTATION_COACH.get(locale) or i18n.REPUTATION_COACH["en"]
    project_path = f"/projects/{active_project_id}" if active_project_id else "/projects"
    report_id = _latest_report_id(db, user)
    report_path = f"/reports/{report_id}" if report_id else project_path
    share_path = f"{project_path}#report-share" if active_project_id else report_path
    publish_ready = bool(mastery_goal.get("publish_ready"))

    full_guide = [
        {
            "step": 1,
            "label": labels["step1_label"],
            "hint": labels["step1_hint"],
            "cta_path": project_path,
            "cta_action": "publish_share",
        },
        {
            "step": 2,
            "label": labels["step2_label"],
            "hint": labels["step2_hint"],
            "cta_path": share_path,
            "cta_action": "publish_share",
        },
        {
            "step": 3,
            "label": labels["step3_label"],
            "hint": labels["step3_hint"],
            "cta_path": "/feed",
            "cta_action": "keep_going",
        },
    ]

    if flags.get("publish") and not flags.get("share"):
        reason = "share_next"
        message = labels["share_next"]
        celebrate = labels["celebrate"]
        cta_action = "publish_share"
        cta_path = share_path
        guide_title = labels["guide_title"]
        guide_steps = full_guide[1:]
    elif publish_ready and not flags.get("publish"):
        reason = "publish_first"
        message = labels["publish_first"]
        celebrate = labels["on_board"] if on_board else labels["celebrate"]
        cta_action = "publish_share"
        cta_path = project_path
        guide_title = labels["guide_title"]
        guide_steps = full_guide
    else:
        reason = "masters_reputation"
        message = labels["masters_intro"]
        celebrate = labels["on_board"] if on_board else labels["celebrate"]
        cta_action = "publish_share"
        cta_path = project_path
        guide_title = labels["guide_title"]
        guide_steps = full_guide

    return {
        "reason": reason,
        "badge": labels["badge"],
        "message": message,
        "celebrate": celebrate,
        "unlock_features": labels["unlock"],
        "cta_action": cta_action,
        "cta_path": cta_path,
        "active_project_id": active_project_id,
        "on_leaderboard": on_board,
        "guide_title": guide_title,
        "guide_steps": guide_steps,
    }


def share_growth_coaching_payload(db: Session, user: User, locale: Locale, flags: dict[str, bool]) -> dict | None:
    """分享完成后的增长教练 — 浏览复盘、复制链接、回广场互动。"""
    if not flags.get("share"):
        return None

    from backend.app.models.growth import ResearchShare

    row = db.execute(
        select(ResearchShare, ResearchReport)
        .join(ResearchReport, ResearchReport.id == ResearchShare.report_id)
        .where(ResearchShare.owner_id == user.id)
        .order_by(ResearchShare.created_at.desc())
        .limit(1)
    ).first()
    if row is None:
        return None

    share, report = row
    from backend.app.services import social_service

    labels = i18n.SHARE_GROWTH_COACH.get(locale) or i18n.SHARE_GROWTH_COACH["en"]
    views = int(share.views or 0)
    follow_counts = social_service.counts(db, user.id)
    followers = int(follow_counts["followers"])
    following = int(follow_counts["following"])
    share_path = f"/share/{share.token}"
    feed_path = f"/feed?highlight={report.id}"
    if views >= 10:
        reason = "amplify"
    elif followers >= 1:
        reason = "first_follower"
    elif following == 0:
        reason = "network_start"
    else:
        reason = "first_views"

    step3_path = "/feed" if following == 0 else feed_path
    step3_label = labels["step3_follow_label"] if following == 0 else labels["step3_label"]
    step3_hint = labels["step3_follow_hint"] if following == 0 else labels["step3_hint"]

    return {
        "reason": reason,
        "badge": labels["badge"],
        "message": labels[reason],
        "guide_title": labels["guide_title"],
        "views": views,
        "followers": followers,
        "following": following,
        "share_url_path": share_path,
        "feed_path": feed_path,
        "profile_path": "/me",
        "following_feed_path": "/me/following",
        "report_title": report.title,
        "guide_steps": [
            {
                "step": 1,
                "label": labels["step1_label"],
                "hint": labels["step1_hint"],
                "cta_path": share_path,
                "cta_action": "keep_going",
            },
            {
                "step": 2,
                "label": labels["step2_label"],
                "hint": labels["step2_hint"],
                "cta_path": share_path,
                "cta_action": "keep_going",
            },
            {
                "step": 3,
                "label": step3_label,
                "hint": step3_hint,
                "cta_path": step3_path,
                "cta_action": "keep_going",
            },
        ],
    }


def mastery_graduation_coaching_payload(
    db: Session,
    user: User,
    locale: Locale,
    flags: dict[str, bool],
    *,
    mastery_goal: dict,
    active_project_id: uuid.UUID | None,
) -> dict | None:
    """五阶段大师路径全部完成且已分享 — 毕业庆祝与进阶指引。"""
    if not flags.get("share"):
        return None

    phases = _mastery_path_phase_rows(
        locale, flags, mastery_goal=mastery_goal, active_project_id=active_project_id
    )
    if not phases or not all(p["done"] for p in phases):
        return None

    from backend.app.services import social_service

    labels = i18n.MASTERY_GRADUATION_COACH.get(locale) or i18n.MASTERY_GRADUATION_COACH["en"]
    on_board = bool(mastery_goal.get("on_leaderboard"))
    rank = mastery_goal.get("leaderboard_rank")
    followers = int(social_service.counts(db, user.id)["followers"])
    graduated = int(mastery_goal.get("paper_graduated_count") or 0)
    project_path = f"/projects/{active_project_id}" if active_project_id else "/projects"

    return {
        "badge": labels["badge"],
        "celebrate": labels["celebrate"],
        "message": labels["on_board"] if on_board else labels["off_board"],
        "guide_title": labels["guide_title"],
        "done_count": len(phases),
        "total": len(phases),
        "paper_graduated_count": graduated,
        "on_leaderboard": on_board,
        "leaderboard_rank": rank,
        "followers": followers,
        "cta_action": "view_board",
        "cta_path": "/leaderboards/paper_mastery",
        "profile_path": "/me",
        "guide_steps": [
            {
                "step": 1,
                "label": labels["step1_label"],
                "hint": labels["step1_hint"],
                "cta_path": project_path,
                "cta_action": "run_paper",
            },
            {
                "step": 2,
                "label": labels["step2_label"],
                "hint": labels["step2_hint"],
                "cta_path": "/me",
                "cta_action": "keep_going",
            },
            {
                "step": 3,
                "label": labels["step3_label"],
                "hint": labels["step3_hint"],
                "cta_path": "/templates?focus=vol-regime",
                "cta_action": "create_project",
            },
        ],
    }


def beginner_sprint_payload(
    user: User,
    locale: Locale,
    flags: dict[str, bool],
    *,
    challenge_enrolled: bool,
    quickstart_guide: dict | None,
) -> dict | None:
    """注册后 7 天内 — 3 步上手与 30 天挑战联动冲刺。"""
    if flags.get("report") or quickstart_guide is None:
        return None

    from datetime import datetime, timezone

    created = user.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    day = min(7, max(1, (datetime.now(timezone.utc) - created).days + 1))

    labels = i18n.BEGINNER_SPRINT.get(locale) or i18n.BEGINNER_SPRINT["en"]
    if day <= 3:
        phase = "quickstart"
        message = labels["days_1_3"]
        cta_action = "create_project"
    elif not challenge_enrolled:
        phase = "enroll"
        message = labels["days_4_7_enroll"]
        cta_action = "enroll_challenge"
    else:
        phase = "challenge"
        message = labels["days_4_7_active"]
        cta_action = "view_challenge"

    return {
        "sprint_day": day,
        "sprint_total": 7,
        "phase": phase,
        "title": labels["title"].format(day=day),
        "message": message,
        "challenge_enrolled": challenge_enrolled,
        "challenge_code": "30d-research",
        "cta_path": "/challenges",
        "cta_action": cta_action,
    }


def mastery_overview_payload(
    db: Session,
    user: User,
    locale: Locale,
    flags: dict[str, bool],
    *,
    mastery_goal: dict,
    active_project_id: uuid.UUID | None,
) -> dict | None:
    """新手大师路径一页纸总览 — 五阶段全部完成前展示。"""
    labels = i18n.MASTERY_OVERVIEW.get(locale) or i18n.MASTERY_OVERVIEW["en"]
    phases = _mastery_path_phase_rows(
        locale, flags, mastery_goal=mastery_goal, active_project_id=active_project_id
    )
    done_count = sum(1 for p in phases if p["done"])
    if done_count >= len(phases):
        return None

    current_index = next((i for i, p in enumerate(phases) if not p["done"]), len(phases) - 1)
    report_id = _latest_report_id(db, user)
    publish_ready = bool(mastery_goal.get("publish_ready"))
    share_ready = bool(flags.get("report") and publish_ready and report_id is not None)
    return {
        "title": labels["title"],
        "subtitle": labels["subtitle"],
        "current_badge": labels["current_badge"],
        "print_title": labels["print_title"],
        "phases": phases,
        "done_count": done_count,
        "total": len(phases),
        "current_index": current_index,
        "share_ready": share_ready,
        "share_report_id": report_id if share_ready else None,
        "share_hint": labels["share_hint"] if share_ready else labels["share_locked"],
        "share_cta": labels["share_cta"],
    }


def _mastery_goal_hint(
    locale: Locale,
    *,
    on_board: bool,
    rank: int | None,
    graduated: int,
    paper_ready: bool,
    mastery_next: str | None,
    progress_pct: int,
    board_ctx: dict,
) -> str:
    hints = i18n.MASTERY_GOAL_HINT.get(locale) or i18n.MASTERY_GOAL_HINT["en"]
    labels = i18n.MASTERY_STAGE_LABEL.get(locale) or i18n.MASTERY_STAGE_LABEL["en"]
    limit = int(board_ctx.get("board_limit") or 50)
    if on_board and rank:
        return hints["on_board"].format(rank=rank, count=graduated)
    if graduated > 0 and not on_board:
        cutoff = board_ctx.get("cutoff_graduated")
        needed = board_ctx.get("graduated_needed")
        if needed and needed > 0 and cutoff is not None:
            return hints["outside_board_graduated"].format(
                limit=limit, cutoff=cutoff, count=graduated, needed=needed
            )
        if board_ctx.get("needs_tracking_boost"):
            return hints["outside_board_tracking"].format(limit=limit, count=graduated)
        outside = board_ctx.get("ranks_outside_board")
        if rank and outside and outside > 0:
            return hints["outside_board_rank"].format(rank=rank, limit=limit, outside=outside)
    if paper_ready:
        return hints["paper_ready"]
    if mastery_next:
        next_label = labels.get(mastery_next, mastery_next)
        return hints["in_progress"].format(next=next_label, pct=progress_pct)
    return hints["start"]


def _mastery_goal_payload(db: Session, user: User, locale: Locale) -> dict:
    from backend.app.services import leaderboard_service, research_quality_service as rqs

    counts = rqs.user_paper_mastery_counts(db, user.id)
    graduated = counts["paper_graduated_count"]
    tracking = counts["paper_tracking_count"]
    board_ctx = leaderboard_service.paper_mastery_board_context(db, user.id)
    rank = board_ctx["leaderboard_rank"]
    on_board = board_ctx["on_leaderboard"]

    active_id = _active_project_id(db, user)
    mastery_stage = None
    mastery_next_action = None
    mastery_progress_pct = 0
    paper_ready = False
    publish_ready = False

    if active_id:
        q = rqs.project_quality_payload(db, active_id, locale=locale)
        m = q.get("mastery") or {}
        mastery_stage = m.get("stage")
        mastery_next_action = m.get("next_action")
        mastery_progress_pct = int(m.get("progress_pct") or 0)
        paper_ready = bool(q.get("paper_ready"))
        feed = q.get("feed_preview") or {}
        publish_ready = bool(feed.get("publish_ready"))

    hint = _mastery_goal_hint(
        locale,
        on_board=on_board,
        rank=rank,
        graduated=graduated,
        paper_ready=paper_ready,
        mastery_next=mastery_next_action,
        progress_pct=mastery_progress_pct,
        board_ctx=board_ctx,
    )

    challenge_paper: list[dict] = []
    from backend.app.services import challenge_service

    ch_prog = challenge_service.progress_if_enrolled(db, user)
    if ch_prog:
        for m in ch_prog["milestones"]:
            if m["code"] in ("first_paper_order", "paper_graduated"):
                titles = i18n.MILESTONE_TITLES.get(m["code"], {})
                title = titles.get(locale) or m["title"]
                ms = m.get("mastery_stage") or i18n.MILESTONE_MASTERY_STAGES.get(m["code"])
                stage_labels = i18n.MASTERY_STAGE_LABEL.get(locale) or i18n.MASTERY_STAGE_LABEL["en"]
                challenge_paper.append(
                    {
                        "code": m["code"],
                        "day": m["day"],
                        "title": title,
                        "completed": m["completed"],
                        "mastery_stage": ms,
                        "mastery_stage_label": stage_labels.get(ms, ms) if ms else None,
                    }
                )

    return {
        "paper_graduated_count": graduated,
        "paper_tracking_count": tracking,
        "on_leaderboard": on_board,
        "leaderboard_rank": rank,
        "mastery_stage": mastery_stage,
        "mastery_next_action": mastery_next_action,
        "mastery_progress_pct": mastery_progress_pct,
        "paper_ready": paper_ready,
        "publish_ready": publish_ready,
        "hint": hint,
        "challenge_paper_milestones": challenge_paper,
        "board_limit": board_ctx["board_limit"],
        "cutoff_graduated": board_ctx["cutoff_graduated"],
        "graduated_needed": board_ctx["graduated_needed"],
        "needs_tracking_boost": board_ctx["needs_tracking_boost"],
        "ranks_outside_board": board_ctx["ranks_outside_board"],
    }


def research_journey(
    db: Session, user: User, locale: Locale = "en", checkout_plan: str | None = None
) -> dict:
    """七步研究闭环进度 (工作台进度环)。"""
    flags = _journey_flags(db, user)
    labels = i18n.JOURNEY_STEPS.get(locale) or i18n.JOURNEY_STEPS["en"]

    challenge_by_journey: dict[str, list[dict]] = {}
    challenge_enrolled = False
    challenge_code = None
    challenge_completed_count = 0
    challenge_total = 0
    from backend.app.services import challenge_service

    ch_prog = challenge_service.progress_if_enrolled(db, user)
    if ch_prog:
        challenge_enrolled = True
        challenge_code = ch_prog["code"]
        challenge_completed_count = ch_prog["completed_count"]
        challenge_total = ch_prog["total"]
        for m in ch_prog["milestones"]:
            jk = m.get("journey_key")
            if not jk:
                continue
            challenge_by_journey.setdefault(jk, []).append(
                {
                    "code": m["code"],
                    "day": m["day"],
                    "title": m["title"],
                    "completed": m["completed"],
                }
            )

    steps = []
    for k in JOURNEY_STEP_KEYS:
        steps.append(
            {
                "key": k,
                "label": labels[k],
                "done": flags[k],
                "challenge_milestones": challenge_by_journey.get(k, []),
            }
        )
    done_count = sum(1 for s in steps if s["done"])
    from backend.app.services import challenge_service, regime_alert_service

    active_id = _active_project_id(db, user)
    mastery_goal = _mastery_goal_payload(db, user, locale)
    attention_alerts = regime_alert_service.list_attention_alerts(db, user, locale)
    attention_alerts = challenge_service.enrich_attention_alerts(
        db, user, locale, attention_alerts
    )
    challenge_paper_coaching = challenge_service.challenge_paper_coaching_payload(
        db,
        user,
        locale,
        attention_alerts=attention_alerts,
        active_project_id=active_id,
        paper_ready=bool(mastery_goal.get("paper_ready")),
        mastery_next_action=mastery_goal.get("mastery_next_action"),
    )

    from backend.app.services import membership_service as ms

    upgrade_coaching = ms.upgrade_coaching_payload(
        db,
        user,
        locale,
        mastery_goal=mastery_goal,
        challenge_paper_coaching=challenge_paper_coaching,
    )

    from backend.app.services import market_data_policy as mdp

    active_symbol = None
    if active_id:
        proj = db.get(ResearchProject, active_id)
        active_symbol = proj.symbol if proj else None

    market_data_coaching = mdp.market_data_coaching_payload(
        db,
        user,
        locale,
        symbol=active_symbol,
        has_active_research=done_count >= 1,
    )

    # 新手友好：大师路径 Pro 升级优先于行情深度 Plus 引导，避免双卡堆叠
    if upgrade_coaching and market_data_coaching:
        if upgrade_coaching["target_tier"] >= market_data_coaching["target_tier"]:
            market_data_coaching = None

    checkout_coaching = ms.post_checkout_coaching_payload(
        db,
        user,
        locale,
        checkout_plan,
        mastery_goal=mastery_goal,
        active_project_id=active_id,
        done_count=done_count,
    )
    if checkout_coaching:
        upgrade_coaching = None
        market_data_coaching = None

    nxt = next_step(db, user, locale)
    quickstart_guide = quickstart_guide_payload(
        locale,
        flags,
        active_project_id=active_id,
        recommended_template=nxt.get("recommended_template"),
    )
    first_project_coaching = first_project_coaching_payload(
        db,
        user,
        locale,
        flags,
        active_project_id=active_id,
    )
    first_report_coaching = first_report_coaching_payload(
        db,
        user,
        locale,
        flags,
        mastery_goal=mastery_goal,
        active_project_id=active_id,
    )
    beginner_sprint = beginner_sprint_payload(
        user,
        locale,
        flags,
        challenge_enrolled=challenge_enrolled,
        quickstart_guide=quickstart_guide,
    )
    mastery_overview = mastery_overview_payload(
        db,
        user,
        locale,
        flags,
        mastery_goal=mastery_goal,
        active_project_id=active_id,
    )
    reputation_coaching = reputation_coaching_payload(
        db,
        user,
        locale,
        flags,
        mastery_goal=mastery_goal,
        active_project_id=active_id,
    )
    share_growth_coaching = share_growth_coaching_payload(db, user, locale, flags)
    mastery_graduation_coaching = mastery_graduation_coaching_payload(
        db,
        user,
        locale,
        flags,
        mastery_goal=mastery_goal,
        active_project_id=active_id,
    )

    return {
        "done_count": done_count,
        "total": len(steps),
        "steps": steps,
        "active_project_id": active_id,
        "challenge_enrolled": challenge_enrolled,
        "challenge_code": challenge_code,
        "challenge_completed_count": challenge_completed_count,
        "challenge_total": challenge_total,
        "mastery_goal": mastery_goal,
        "attention_alerts": attention_alerts,
        "challenge_paper_coaching": challenge_paper_coaching,
        "upgrade_coaching": upgrade_coaching,
        "market_data_coaching": market_data_coaching,
        "checkout_coaching": checkout_coaching,
        "quickstart_guide": quickstart_guide,
        "first_project_coaching": first_project_coaching,
        "first_report_coaching": first_report_coaching,
        "beginner_sprint": beginner_sprint,
        "mastery_overview": mastery_overview,
        "reputation_coaching": reputation_coaching,
        "share_growth_coaching": share_growth_coaching,
        "mastery_graduation_coaching": mastery_graduation_coaching,
    }

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
        picks_data = template_service.regime_template_picks(db, user, tier, locale)
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
    return {
        "done_count": done_count,
        "total": len(steps),
        "steps": steps,
        "active_project_id": _active_project_id(db, user),
        "challenge_enrolled": challenge_enrolled,
        "challenge_code": challenge_code,
        "challenge_completed_count": challenge_completed_count,
        "challenge_total": challenge_total,
        "mastery_goal": _mastery_goal_payload(db, user, locale),
    }

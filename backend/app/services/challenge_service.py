"""30 天研究挑战业务逻辑 (Sprint 8)。

里程碑可自动判定 (按用户产物统计), 不需手动打卡。给小白明确的节奏感:
Day1 第一个因子 → Day7 首次 OOS → Day15 组合因子 → Day30 研究报告。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.challenge import Challenge, ChallengeProgress
from backend.app.models.execution import PaperOrder
from backend.app.models.factor import Factor, FactorKind
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.i18n.content import MILESTONE_JOURNEY_KEYS, MILESTONE_MASTERY_STAGES, MILESTONE_TITLES
from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.services import growth_service

DEFAULT_CODE = "30d-research"
DEFAULT_MILESTONES = [
    {"day": 1, "code": "first_factor", "title": "创建第一个因子", "check": "factor", "reward_points": 20},
    {"day": 7, "code": "first_oos", "title": "完成第一次科学验证 (OOS)", "check": "validation_success", "reward_points": 40},
    {"day": 15, "code": "stack_factor", "title": "创建第一个组合因子", "check": "stack_factor", "reward_points": 40},
    {"day": 22, "code": "first_paper_order", "title": "下第一笔 Paper 模拟单", "check": "paper_order", "reward_points": 50},
    {"day": 28, "code": "paper_graduated", "title": "因子通过 Paper 毕业线", "check": "paper_graduated", "reward_points": 80},
    {"day": 20, "code": "network_radar", "title": "关注 3 位研究员", "check": "following_three", "reward_points": 40},
    {"day": 29, "code": "research_share", "title": "生成第一份分享卡片", "check": "research_share", "reward_points": 50},
    {"day": 30, "code": "first_report", "title": "产出第一份研究报告", "check": "report", "reward_points": 100},
]
CHALLENGE_COMPLETE_BONUS = 200  # 全部完成额外奖励


class ChallengeNotFoundError(Exception):
    pass


class ChallengeNotCompletedError(Exception):
    pass


def _merge_default_milestones(db: Session, ch: Challenge) -> None:
    """已有挑战补全 Paper 大师路径里程碑 (幂等)。"""
    existing = {m["code"] for m in ch.milestones}
    merged = list(ch.milestones)
    changed = False
    for m in DEFAULT_MILESTONES:
        if m["code"] not in existing:
            merged.append(dict(m))
            changed = True
    if changed:
        merged.sort(key=lambda x: int(x.get("day", 0)))
        ch.milestones = merged
        db.commit()


def seed_default_challenge(db: Session) -> dict:
    existing = db.execute(
        select(Challenge).where(Challenge.code == DEFAULT_CODE)
    ).scalar_one_or_none()
    if existing:
        _merge_default_milestones(db, existing)
        return {"created": False, "code": DEFAULT_CODE, "id": str(existing.id)}
    ch = Challenge(
        code=DEFAULT_CODE,
        title="30 天研究挑战",
        description="从第一个因子到第一份研究报告, 30 天完成你的第一个量化研究项目。",
        days=30,
        milestones=DEFAULT_MILESTONES,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return {"created": True, "code": DEFAULT_CODE, "id": str(ch.id)}


def list_challenges(db: Session) -> list[Challenge]:
    rows = list(db.execute(select(Challenge).order_by(Challenge.created_at.asc())).scalars().all())
    if not rows:
        seed_default_challenge(db)
        rows = list(db.execute(select(Challenge).order_by(Challenge.created_at.asc())).scalars().all())
    else:
        for ch in rows:
            if ch.code == DEFAULT_CODE:
                _merge_default_milestones(db, ch)
    return rows


def get_by_code(db: Session, code: str) -> Challenge:
    ch = db.execute(select(Challenge).where(Challenge.code == code)).scalar_one_or_none()
    if ch is None:
        raise ChallengeNotFoundError(code)
    return ch


def _count(db: Session, stmt) -> int:
    return int(db.execute(stmt).scalar_one() or 0)


def _any_factor_paper_graduated(db: Session, uid: uuid.UUID) -> bool:
    """True if any owned factor passes Paper graduation — short-circuit on first hit.

    Prefer shared mastery counts (session-cached) so journey + challenge do not
    re-walk assessments. Fallback: validated factors only, cap 12.
    """
    from backend.app.services import research_quality_service as rqs

    counts = rqs.user_paper_mastery_counts(db, uid)
    if int(counts.get("paper_graduated_count") or 0) > 0:
        return True
    # Counts already scanned all validated factors; zero means none graduated.
    return False


def _user_stats(db: Session, uid: uuid.UUID) -> dict:
    from backend.app.models.growth import ResearchShare
    from backend.app.services import social_service

    following = int(social_service.counts(db, uid)["following"])
    return {
        "factor": _count(db, select(func.count(Factor.id)).where(Factor.owner_id == uid)),
        "stack_factor": _count(
            db,
            select(func.count(Factor.id)).where(
                Factor.owner_id == uid, Factor.kind == FactorKind.STACK.value
            ),
        ),
        "validation_success": _count(
            db,
            select(func.count(Validation.id)).where(
                Validation.owner_id == uid,
                Validation.status == ValidationStatus.SUCCESS.value,
            ),
        ),
        "report": _count(
            db, select(func.count(ResearchReport.id)).where(ResearchReport.owner_id == uid)
        ),
        "paper_order": _count(
            db, select(func.count(PaperOrder.id)).where(PaperOrder.user_id == uid)
        ),
        "paper_graduated": 1 if _any_factor_paper_graduated(db, uid) else 0,
        "following_three": 1 if following >= 3 else 0,
        "research_share": _count(
            db, select(func.count(ResearchShare.id)).where(ResearchShare.owner_id == uid)
        ),
    }


def is_enrolled(db: Session, user: User, code: str = DEFAULT_CODE) -> bool:
    try:
        ch = get_by_code(db, code)
    except ChallengeNotFoundError:
        return False
    prog = db.execute(
        select(ChallengeProgress).where(
            ChallengeProgress.user_id == user.id,
            ChallengeProgress.challenge_id == ch.id,
        )
    ).scalar_one_or_none()
    return prog is not None


def progress_if_enrolled(db: Session, user: User, code: str = DEFAULT_CODE) -> dict | None:
    """已报名才返回进度 (不自动报名)。"""
    if not is_enrolled(db, user, code):
        return None
    return evaluate(db, user, code)


def enroll(db: Session, user: User, code: str) -> ChallengeProgress:
    ch = get_by_code(db, code)
    prog = db.execute(
        select(ChallengeProgress).where(
            ChallengeProgress.user_id == user.id, ChallengeProgress.challenge_id == ch.id
        )
    ).scalar_one_or_none()
    if prog is None:
        prog = ChallengeProgress(user_id=user.id, challenge_id=ch.id, completed=[])
        db.add(prog)
        db.commit()
        db.refresh(prog)
    return prog


def _pending_hint(db: Session, user: User, code: str, *, done: bool) -> tuple[str | None, str | None]:
    """User-facing why a milestone is still open (zh, en).

    Keep this cheap: progress is polled often; never run full paper assessment
    loops here (that previously caused Cloudflare 502 timeouts).
    """
    if done:
        return None, None
    if code == "first_paper_order":
        return (
            "还没有模拟成交单。请到「模拟交易」或项目 Paper 面板下一笔模拟单（不涉及真钱）。",
            "No paper order yet. Place one in Paper Trading or the project Paper panel (no real money).",
        )
    if code == "paper_graduated":
        return (
            "暂无因子达到 Paper 毕业线。请在项目质量面板查看差距（样本外夏普、稳健性、换手、最低成交次数等）。",
            "No factor has passed the Paper graduation line yet. Check the project quality panel for gaps (OOS Sharpe, robustness, turnover, min trades).",
        )
    if code == "network_radar":
        return (
            "还需要关注满 3 位研究员。可去广场筛选活跃研究员。",
            "Follow 3 researchers on the feed to complete this milestone.",
        )
    if code == "stack_factor":
        return (
            "还没有组合因子。打开项目里的因子实验室，用组合模式创建。",
            "No stacked factor yet. Create one in Factor Lab (stack mode).",
        )
    return None, None


def evaluate(db: Session, user: User, code: str) -> dict:
    """按当前产物重算里程碑完成情况, 持久化并返回带状态的进度。"""
    cache_key = ("challenge_evaluate", str(user.id), code)
    cached = db.info.get(cache_key)
    if cached is not None:
        return cached

    ch = get_by_code(db, code)
    prog = enroll(db, user, code)
    stats = _user_stats(db, user.id)
    rewarded = set(prog.rewarded or [])

    milestones_status = []
    done_codes = []
    newly_awarded = 0
    for m in ch.milestones:
        done = stats.get(m["check"], 0) >= 1
        if done:
            done_codes.append(m["code"])
            if m["code"] not in rewarded:
                pts = int(m.get("reward_points", 0))
                if pts:
                    growth_service.award_reward_points(db, user, pts, commit=False)
                    newly_awarded += pts
                rewarded.add(m["code"])
        hint_zh, hint_en = _pending_hint(db, user, m["code"], done=done)
        milestones_status.append(
            {
                "day": m["day"],
                "code": m["code"],
                "title": m["title"],
                "completed": done,
                "reward_points": int(m.get("reward_points", 0)),
                "journey_key": MILESTONE_JOURNEY_KEYS.get(m["code"]),
                "mastery_stage": MILESTONE_MASTERY_STAGES.get(m["code"]),
                "pending_hint_zh": hint_zh,
                "pending_hint_en": hint_en,
            }
        )

    total = len(ch.milestones)
    all_done = len(done_codes) == total and total > 0

    if all_done and not prog.certificate_code:
        prog.certificate_code = f"QLAB-{code.upper()}-{user.username}-{uuid.uuid4().hex[:6].upper()}"
        prog.completed_at = datetime.now(timezone.utc)
        growth_service.award_reward_points(db, user, CHALLENGE_COMPLETE_BONUS, commit=False)
        newly_awarded += CHALLENGE_COMPLETE_BONUS

    # Keep historical certificate_code in DB, but only expose when currently complete.
    visible_cert = prog.certificate_code if all_done else None
    if not all_done:
        prog.completed_at = None

    prog.completed = done_codes
    prog.rewarded = sorted(rewarded)
    db.commit()
    db.refresh(prog)

    out = {
        "code": ch.code,
        "title": ch.title,
        "days": ch.days,
        "completed_count": len(done_codes),
        "total": total,
        "percent": round(100.0 * len(done_codes) / total, 1) if total else 0.0,
        "milestones": milestones_status,
        "enrolled_at": prog.enrolled_at,
        "newly_awarded_points": newly_awarded,
        "reward_points": user.reward_points,
        "certificate_code": visible_cert,
        "certificate_valid": bool(all_done and prog.certificate_code),
        "completed_at": prog.completed_at if all_done else None,
    }
    db.info[cache_key] = out
    return out


def get_certificate(db: Session, user: User, code: str) -> dict:
    """领取证书 (需挑战当前全部里程碑完成)。"""
    res = evaluate(db, user, code)
    if not res.get("certificate_valid") or not res.get("certificate_code"):
        raise ChallengeNotCompletedError(code)
    return {
        "certificate_code": res["certificate_code"],
        "challenge_title": res["title"],
        "username": user.username,
        "completed_at": res["completed_at"],
    }


_PAPER_MILESTONE_CODES = ("first_paper_order", "paper_graduated")
_SHARE_MILESTONE_CODES = ("network_radar", "research_share")


def _challenge_milestones_payload(
    prog: dict,
    codes: tuple[str, ...],
    locale: Locale,
) -> list[dict]:
    out: list[dict] = []
    for m in prog["milestones"]:
        if m["code"] not in codes:
            continue
        titles = MILESTONE_TITLES.get(m["code"], {})
        title = titles.get(locale) or m["title"]
        ms = m.get("mastery_stage") or MILESTONE_MASTERY_STAGES.get(m["code"])
        stage_labels = i18n.MASTERY_STAGE_LABEL.get(locale) or i18n.MASTERY_STAGE_LABEL["en"]
        out.append(
            {
                "code": m["code"],
                "day": m["day"],
                "title": title,
                "completed": m["completed"],
                "mastery_stage": ms,
                "mastery_stage_label": stage_labels.get(ms, ms) if ms else None,
            }
        )
    return out


def _pending_paper_milestones(prog: dict) -> list[dict]:
    return [
        m
        for m in prog["milestones"]
        if m["code"] in _PAPER_MILESTONE_CODES and not m["completed"]
    ]


def challenge_paper_milestones_for_journey(db: Session, user: User, locale: Locale) -> list[dict]:
    prog = progress_if_enrolled(db, user)
    if not prog:
        return []
    return _challenge_milestones_payload(prog, _PAPER_MILESTONE_CODES, locale)


def challenge_share_milestones_for_journey(db: Session, user: User, locale: Locale) -> list[dict]:
    prog = progress_if_enrolled(db, user)
    if not prog:
        return []
    return _challenge_milestones_payload(prog, _SHARE_MILESTONE_CODES, locale)


def alert_challenge_hints(db: Session, user: User, locale: Locale = "en") -> dict[str, str]:
    """主动提醒 kind → 30 天挑战 Paper 里程碑联动文案。"""
    prog = progress_if_enrolled(db, user)
    if not prog:
        return {}
    pending_codes = {m["code"] for m in _pending_paper_milestones(prog)}
    if not pending_codes:
        return {}
    labels = i18n.ALERT_CHALLENGE_HINT.get(locale) or i18n.ALERT_CHALLENGE_HINT["en"]
    hints: dict[str, str] = {}
    if "first_paper_order" in pending_codes:
        hints["regime_shift"] = labels["regime_shift_d22"]
        hints["weak_regime_fit"] = labels["weak_fit_d22"]
    if "paper_graduated" in pending_codes:
        hints["paper_decay"] = labels["paper_decay_d28"]
        if "regime_shift" not in hints:
            hints["regime_shift"] = labels["regime_shift_d28"]
    return hints


def enrich_attention_alerts(
    db: Session,
    user: User,
    locale: Locale,
    alerts: list[dict],
) -> list[dict]:
    hints = alert_challenge_hints(db, user, locale)
    if not hints:
        return alerts
    out: list[dict] = []
    for alert in alerts:
        hint = hints.get(alert.get("kind", ""))
        if hint:
            out.append({**alert, "challenge_hint": hint})
        else:
            out.append(alert)
    return out


def challenge_paper_coaching_payload(
    db: Session,
    user: User,
    locale: Locale,
    *,
    attention_alerts: list[dict],
    active_project_id: uuid.UUID | None,
    paper_ready: bool = False,
    mastery_next_action: str | None = None,
) -> dict | None:
    """30 天挑战 Paper 里程碑 × 主动提醒联合教练。"""
    prog = progress_if_enrolled(db, user)
    if not prog:
        return None
    pending = _pending_paper_milestones(prog)
    if not pending:
        return None

    next_m = pending[0]
    code = next_m["code"]
    titles = MILESTONE_TITLES.get(code, {})
    title = titles.get(locale) or next_m["title"]
    alert_kinds = {a.get("kind") for a in attention_alerts}
    has_attention = bool(attention_alerts)
    labels = i18n.CHALLENGE_PAPER_COACH.get(locale) or i18n.CHALLENGE_PAPER_COACH["en"]

    if code == "first_paper_order":
        if has_attention:
            message_key = "d22_with_attention"
        elif paper_ready:
            message_key = "d22_ready"
        else:
            message_key = "d22_not_ready"
        cta_action = "run_paper" if paper_ready else (mastery_next_action or "run_validation")
    else:
        if "paper_decay" in alert_kinds:
            message_key = "d28_decay"
        elif paper_ready:
            message_key = "d28_ready"
        else:
            message_key = "d28_not_ready"
        cta_action = (
            "revalidate_decay"
            if "paper_decay" in alert_kinds
            else (mastery_next_action or "run_validation")
        )

    if code == "first_paper_order" and not paper_ready and not has_attention:
        return None

    if code == "paper_graduated" and not has_attention and not paper_ready:
        return None

    cta_path = f"/projects/{active_project_id}" if active_project_id else "/challenges"
    return {
        "enrolled": True,
        "next_code": code,
        "next_day": next_m["day"],
        "next_title": title,
        "message": labels[message_key].format(
            day=next_m["day"],
            title=title,
            attention_count=len(attention_alerts),
        ),
        "cta_path": cta_path,
        "cta_action": cta_action,
        "attention_linked": has_attention,
        "linked_alert_kinds": sorted(alert_kinds),
    }

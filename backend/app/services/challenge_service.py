"""30 天研究挑战业务逻辑 (Sprint 8)。

里程碑可自动判定 (按用户产物统计), 不需手动打卡。给小白明确的节奏感:
Day1 第一个因子 → Day7 首次 OOS → Day15 组合因子 → Day30 研究报告。
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.challenge import Challenge, ChallengeProgress
from backend.app.models.factor import Factor, FactorKind
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus

DEFAULT_CODE = "30d-research"
DEFAULT_MILESTONES = [
    {"day": 1, "code": "first_factor", "title": "创建第一个因子", "check": "factor"},
    {"day": 7, "code": "first_oos", "title": "完成第一次科学验证 (OOS)", "check": "validation_success"},
    {"day": 15, "code": "stack_factor", "title": "创建第一个组合因子", "check": "stack_factor"},
    {"day": 30, "code": "first_report", "title": "产出第一份研究报告", "check": "report"},
]


class ChallengeNotFoundError(Exception):
    pass


def seed_default_challenge(db: Session) -> dict:
    existing = db.execute(
        select(Challenge).where(Challenge.code == DEFAULT_CODE)
    ).scalar_one_or_none()
    if existing:
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
    return list(db.execute(select(Challenge).order_by(Challenge.created_at.asc())).scalars().all())


def get_by_code(db: Session, code: str) -> Challenge:
    ch = db.execute(select(Challenge).where(Challenge.code == code)).scalar_one_or_none()
    if ch is None:
        raise ChallengeNotFoundError(code)
    return ch


def _count(db: Session, stmt) -> int:
    return int(db.execute(stmt).scalar_one() or 0)


def _user_stats(db: Session, uid: uuid.UUID) -> dict:
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
    }


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


def evaluate(db: Session, user: User, code: str) -> dict:
    """按当前产物重算里程碑完成情况, 持久化并返回带状态的进度。"""
    ch = get_by_code(db, code)
    prog = enroll(db, user, code)
    stats = _user_stats(db, user.id)

    milestones_status = []
    done_codes = []
    for m in ch.milestones:
        done = stats.get(m["check"], 0) >= 1
        if done:
            done_codes.append(m["code"])
        milestones_status.append(
            {"day": m["day"], "code": m["code"], "title": m["title"], "completed": done}
        )

    prog.completed = done_codes
    db.commit()
    db.refresh(prog)

    total = len(ch.milestones)
    return {
        "code": ch.code,
        "title": ch.title,
        "days": ch.days,
        "completed_count": len(done_codes),
        "total": total,
        "percent": round(100.0 * len(done_codes) / total, 1) if total else 0.0,
        "milestones": milestones_status,
        "enrolled_at": prog.enrolled_at,
    }

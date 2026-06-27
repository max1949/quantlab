"""竞技系统业务逻辑 (Sprint 6)。

提交 = 把一次成功的科学验证 (Sprint 5) 计入赛季: 用 engine.scoring 算 Research Score
(五维 + 动态衰减), 落库并刷新榜单。同时回填用户的 research_score (取历史最佳)。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine.scoring import research_score
from backend.app.models.competition import Season, SeasonStatus, Submission
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus


class SeasonNotFoundError(Exception):
    pass


class SeasonClosedError(Exception):
    pass


class SeasonNameTakenError(Exception):
    pass


class ValidationNotEligibleError(Exception):
    """验证不存在 / 非本人 / 未成功。"""


class AlreadySubmittedError(Exception):
    pass


def list_seasons(db: Session) -> list[Season]:
    return list(
        db.execute(select(Season).order_by(Season.created_at.desc())).scalars().all()
    )


def get_season(db: Session, season_id: uuid.UUID) -> Season:
    season = db.get(Season, season_id)
    if season is None:
        raise SeasonNotFoundError(str(season_id))
    return season


def create_season(db: Session, name: str, description: str = "") -> Season:
    if db.execute(select(Season.id).where(Season.name == name)).first():
        raise SeasonNameTakenError(name)
    season = Season(name=name, description=description, status=SeasonStatus.OPEN.value)
    db.add(season)
    db.commit()
    db.refresh(season)
    return season


def seed_default_season(db: Session, name: str = "2026-S1") -> dict:
    existing = db.execute(select(Season).where(Season.name == name)).scalar_one_or_none()
    if existing:
        return {"created": False, "id": str(existing.id), "name": name}
    s = create_season(db, name, "首个公开赛季: 提交通过科学验证的因子, 比稳健性与研究质量。")
    return {"created": True, "id": str(s.id), "name": name}


def _validation_payload(v: Validation) -> dict:
    return {
        "oos": v.oos,
        "walk_forward": v.walk_forward,
        "sensitivity": v.sensitivity,
    }


def submit(
    db: Session, owner: User, season_id: uuid.UUID, validation_id: uuid.UUID
) -> Submission:
    season = get_season(db, season_id)
    if season.status != SeasonStatus.OPEN.value:
        raise SeasonClosedError(str(season_id))

    v = db.get(Validation, validation_id)
    if v is None or v.owner_id != owner.id or v.status != ValidationStatus.SUCCESS.value:
        raise ValidationNotEligibleError(str(validation_id))

    dup = db.execute(
        select(Submission.id).where(
            Submission.season_id == season_id,
            Submission.validation_id == validation_id,
        )
    ).first()
    if dup:
        raise AlreadySubmittedError(str(validation_id))

    score = research_score(_validation_payload(v))

    sub = Submission(
        season_id=season_id,
        owner_id=owner.id,
        factor_id=v.factor_id,
        validation_id=validation_id,
        symbol=v.symbol,
        base_score=score["base_score"],
        decay_factor=score["decay_factor"],
        final_score=score["final_score"],
        dimensions=score["dimensions"],
    )
    db.add(sub)

    # 回填用户 research_score: 取历史最佳 (Sprint 1 预留字段在此启用)
    if score["final_score"] > (owner.research_score or 0.0):
        owner.research_score = score["final_score"]

    db.commit()
    db.refresh(sub)
    return sub


def list_my_submissions(
    db: Session, owner_id: uuid.UUID, season_id: uuid.UUID
) -> list[Submission]:
    return list(
        db.execute(
            select(Submission)
            .where(
                Submission.season_id == season_id,
                Submission.owner_id == owner_id,
            )
            .order_by(Submission.final_score.desc())
        )
        .scalars()
        .all()
    )


def leaderboard(db: Session, season_id: uuid.UUID, limit: int = 50) -> list[dict]:
    """按最终分降序的榜单 (含用户名)。"""
    get_season(db, season_id)  # 校验存在
    rows = db.execute(
        select(Submission, User.username)
        .join(User, User.id == Submission.owner_id)
        .where(Submission.season_id == season_id)
        .order_by(Submission.final_score.desc(), Submission.created_at.asc())
        .limit(limit)
    ).all()
    out = []
    for rank, (sub, username) in enumerate(rows, start=1):
        out.append(
            {
                "rank": rank,
                "username": username,
                "factor_id": sub.factor_id,
                "symbol": sub.symbol,
                "base_score": sub.base_score,
                "decay_factor": sub.decay_factor,
                "final_score": sub.final_score,
                "submitted_at": sub.created_at,
            }
        )
    return out

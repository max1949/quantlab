"""全站多维榜单 (Sprint 9A)。

不只看收益, 用多个维度鼓励不同人群 (尤其新人):
- researcher : 研究信用分 (长期研究贡献) —— 平台真正想要的
- contributor: reward_points (活跃参与)
- newcomer   : 近 30 天加入者中的研究信用
- improved   : 近 14 天产出最多 (有效验证 + 报告) 的"进步之星"

与赛季榜 (/seasons/{id}/leaderboard) 并存; 这里是全站、跨赛季的成长榜。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.factor import Factor
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.services.growth_service import EFFECTIVE_GRADES

KINDS = {"researcher", "contributor", "newcomer", "improved", "paper_mastery"}

NEWCOMER_DAYS = 30
IMPROVED_DAYS = 14


def _row(rank: int, user: User, metric_label: str, metric_value) -> dict:
    return {
        "rank": rank,
        "user_id": str(user.id),
        "username": user.username,
        "level": user.level,
        "metric_label": metric_label,
        "metric_value": metric_value,
    }


def leaderboard(db: Session, kind: str, limit: int = 50) -> list[dict]:
    if kind not in KINDS:
        raise ValueError(f"未知榜单: {kind}")

    if kind == "researcher":
        users = db.execute(
            select(User).order_by(User.research_contribution_score.desc(), User.created_at.asc()).limit(limit)
        ).scalars().all()
        return [_row(i + 1, u, "研究信用", round(u.research_contribution_score, 2)) for i, u in enumerate(users)]

    if kind == "contributor":
        users = db.execute(
            select(User).order_by(User.reward_points.desc(), User.created_at.asc()).limit(limit)
        ).scalars().all()
        return [_row(i + 1, u, "活跃积分", u.reward_points) for i, u in enumerate(users)]

    if kind == "newcomer":
        since = datetime.now(timezone.utc) - timedelta(days=NEWCOMER_DAYS)
        users = db.execute(
            select(User)
            .where(User.created_at >= since)
            .order_by(User.research_contribution_score.desc(), User.created_at.asc())
            .limit(limit)
        ).scalars().all()
        return [_row(i + 1, u, "新人研究信用", round(u.research_contribution_score, 2)) for i, u in enumerate(users)]

    if kind == "paper_mastery":
        return _paper_mastery_board(db, limit)

    # improved: 近 IMPROVED_DAYS 天有效验证 (稳健/中等) + 报告
    since = datetime.now(timezone.utc) - timedelta(days=IMPROVED_DAYS)
    val_rows = db.execute(
        select(Validation.owner_id, Validation.robustness)
        .where(
            Validation.status == ValidationStatus.SUCCESS.value,
            Validation.created_at >= since,
        )
    ).all()
    val_counts: dict = {}
    for owner_id, robustness in val_rows:
        if (robustness or {}).get("grade") not in EFFECTIVE_GRADES:
            continue
        val_counts[owner_id] = val_counts.get(owner_id, 0) + 1
    rep_counts = dict(
        db.execute(
            select(ResearchReport.owner_id, func.count(ResearchReport.id))
            .where(ResearchReport.created_at >= since)
            .group_by(ResearchReport.owner_id)
        ).all()
    )
    scores: dict = {}
    for uid, c in val_counts.items():
        scores[uid] = scores.get(uid, 0) + c
    for uid, c in rep_counts.items():
        scores[uid] = scores.get(uid, 0) + c
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    out = []
    for i, (uid, val) in enumerate(ranked):
        user = db.get(User, uid)
        if user is None:
            continue
        out.append(_row(i + 1, user, "近期产出", val))
    return out


def _paper_mastery_board(db: Session, limit: int) -> list[dict]:
    from backend.app.services import research_quality_service as rqs

    owner_ids = list(db.execute(select(Factor.owner_id).distinct()).scalars().all())
    scores: dict = {}
    for uid in owner_ids:
        counts = rqs.user_paper_mastery_counts(db, uid)
        graduated = counts["paper_graduated_count"]
        if graduated <= 0:
            continue
        scores[uid] = (graduated, counts["paper_tracking_count"])

    ranked = sorted(scores.items(), key=lambda kv: (kv[1][0], kv[1][1]), reverse=True)[:limit]
    out: list[dict] = []
    for i, (uid, (graduated, tracking)) in enumerate(ranked):
        user = db.get(User, uid)
        if user is None:
            continue
        label = "Paper毕业因子"
        value = f"{graduated}" + (f" (+{tracking}跟踪)" if tracking else "")
        out.append(_row(i + 1, user, label, value))
    return out

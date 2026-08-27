"""全站多维榜单 (Sprint 9A)。

不只看收益, 用多个维度鼓励不同人群 (尤其新人):
- researcher : 研究信用分 (长期研究贡献) —— 平台真正想要的
- contributor: reward_points (活跃参与)
- newcomer   : 近 30 天加入者中的研究信用
- improved   : 近 14 天产出最多 (有效验证 + 报告) 的"进步之星"

与赛季榜 (/seasons/{id}/leaderboard) 并存; 这里是全站、跨赛季的成长榜。
"""

from __future__ import annotations

import time
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
PAPER_MASTERY_BOARD_LIMIT = 50
# Full-site paper mastery ranking walks every factor owner; cache briefly so
# journey / coaching endpoints do not recompute on every page load.
_PAPER_MASTERY_RANKED_TTL_S = 60.0
_paper_mastery_ranked_cache: dict = {"at": 0.0, "rows": None}


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
        # Min sample for ranking: non-zero research credit (effective validation /
        # report / publish / follow). Boards are not Sharpe-ranked; zero-score
        # accounts must not pad #1–N.
        users = db.execute(
            select(User)
            .where(User.research_contribution_score > 0)
            .order_by(User.research_contribution_score.desc(), User.created_at.asc())
            .limit(limit)
        ).scalars().all()
        return [_row(i + 1, u, "研究信用", round(u.research_contribution_score, 2)) for i, u in enumerate(users)]

    if kind == "contributor":
        users = db.execute(
            select(User)
            .where(User.reward_points > 0)
            .order_by(User.reward_points.desc(), User.created_at.asc())
            .limit(limit)
        ).scalars().all()
        return [_row(i + 1, u, "活跃积分", u.reward_points) for i, u in enumerate(users)]

    if kind == "newcomer":
        since = datetime.now(timezone.utc) - timedelta(days=NEWCOMER_DAYS)
        users = db.execute(
            select(User)
            .where(
                User.created_at >= since,
                User.research_contribution_score > 0,
            )
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


def _paper_mastery_ranked(db: Session) -> list[tuple]:
    """[(user_id, graduated, tracking), ...] 按毕业数、跟踪数降序。"""
    from backend.app.services import research_quality_service as rqs

    sess_key = "paper_mastery_ranked"
    cached = db.info.get(sess_key)
    if cached is not None:
        return cached

    now = time.monotonic()
    global_rows = _paper_mastery_ranked_cache.get("rows")
    if (
        global_rows is not None
        and (now - float(_paper_mastery_ranked_cache.get("at") or 0.0)) < _PAPER_MASTERY_RANKED_TTL_S
    ):
        db.info[sess_key] = global_rows
        return global_rows

    # Only owners with a successful validation can have graduated factors.
    owner_ids = list(
        db.execute(
            select(Factor.owner_id)
            .join(Validation, Validation.factor_id == Factor.id)
            .where(Validation.status == ValidationStatus.SUCCESS.value)
            .distinct()
        ).scalars().all()
    )
    scores: list[tuple] = []
    for uid in owner_ids:
        counts = rqs.user_paper_mastery_counts(db, uid)
        graduated = counts["paper_graduated_count"]
        if graduated > 0:
            scores.append((uid, graduated, counts["paper_tracking_count"]))
    scores.sort(key=lambda row: (row[1], row[2]), reverse=True)
    _paper_mastery_ranked_cache["at"] = now
    _paper_mastery_ranked_cache["rows"] = scores
    db.info[sess_key] = scores
    return scores


def paper_mastery_board_context(
    db: Session, user_id, *, board_limit: int = PAPER_MASTERY_BOARD_LIMIT
) -> dict:
    """Paper 大师榜名次 + 榜外距入榜线差距 (孵化指引)。"""
    from backend.app.services import research_quality_service as rqs

    ranked = _paper_mastery_ranked(db)
    counts = rqs.user_paper_mastery_counts(db, user_id)
    graduated = counts["paper_graduated_count"]
    tracking = counts["paper_tracking_count"]

    rank = None
    for i, (uid, _, _) in enumerate(ranked):
        if uid == user_id:
            rank = i + 1
            break

    on_board = rank is not None and rank <= board_limit
    cutoff_graduated = None
    cutoff_tracking = None
    if ranked:
        idx = min(board_limit - 1, len(ranked) - 1)
        _, cutoff_graduated, cutoff_tracking = ranked[idx]

    graduated_needed = None
    needs_tracking_boost = False
    ranks_outside_board = None

    if graduated > 0 and not on_board:
        if rank is not None:
            ranks_outside_board = max(0, rank - board_limit)
        if cutoff_graduated is not None:
            if graduated < cutoff_graduated:
                graduated_needed = cutoff_graduated - graduated
            elif graduated == cutoff_graduated and tracking <= cutoff_tracking:
                needs_tracking_boost = True
            elif rank is not None and rank > board_limit:
                graduated_needed = 1

    return {
        "board_limit": board_limit,
        "leaderboard_rank": rank,
        "on_leaderboard": on_board,
        "cutoff_graduated": cutoff_graduated,
        "graduated_needed": graduated_needed,
        "needs_tracking_boost": needs_tracking_boost,
        "ranks_outside_board": ranks_outside_board,
        "total_ranked": len(ranked),
    }


def paper_mastery_cutoff_meta(db: Session, *, board_limit: int = PAPER_MASTERY_BOARD_LIMIT) -> dict:
    """Paper 大师榜入榜线 (公开, 用于榜页展示)。"""
    from backend.app.models.user import User

    ranked = _paper_mastery_ranked(db)
    if not ranked:
        return {
            "board_limit": board_limit,
            "total_ranked": 0,
            "board_full": False,
            "cutoff": None,
        }

    idx = min(board_limit - 1, len(ranked) - 1)
    uid, graduated, tracking = ranked[idx]
    holder = db.get(User, uid)
    return {
        "board_limit": board_limit,
        "total_ranked": len(ranked),
        "board_full": len(ranked) >= board_limit,
        "cutoff": {
            "rank": idx + 1,
            "user_id": str(uid),
            "username": holder.username if holder else None,
            "graduated": graduated,
            "tracking": tracking,
        },
    }


def paper_mastery_rank_for_user(db: Session, user_id, *, board_limit: int = PAPER_MASTERY_BOARD_LIMIT) -> tuple[int | None, bool]:
    """用户在全站 Paper 大师榜的名次；on_board 表示是否出现在默认榜单页 (前 board_limit 名)。"""
    ctx = paper_mastery_board_context(db, user_id, board_limit=board_limit)
    return ctx["leaderboard_rank"], ctx["on_leaderboard"]


def _paper_mastery_board(db: Session, limit: int) -> list[dict]:
    from backend.app.models.user import User

    ranked = _paper_mastery_ranked(db)[:limit]
    out: list[dict] = []
    for i, (uid, graduated, tracking) in enumerate(ranked):
        user = db.get(User, uid)
        if user is None:
            continue
        label = "Paper毕业因子"
        value = f"{graduated}" + (f" (+{tracking}跟踪)" if tracking else "")
        out.append(_row(i + 1, user, label, value))
    return out

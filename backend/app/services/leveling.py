"""等级成长规则 (纯逻辑, 无 DB)。

经验值 (experience) 单调累积, 等级由经验阈值推导。这样"成长"是确定且可复现的:
给定经验值即可算出等级,完成任务 → 加经验 → 可能升级。

阈值可调;后续 Sprint 若引入更复杂的成长曲线, 仅改此处即可。
"""

from __future__ import annotations

from backend.app.models.user import UserLevel

# 各等级所需的最低累计经验 (升序)。
LEVEL_THRESHOLDS: dict[UserLevel, int] = {
    UserLevel.L0: 0,
    UserLevel.L1: 100,
    UserLevel.L2: 300,
    UserLevel.L3: 700,
}


def level_for_experience(experience: int) -> UserLevel:
    """根据累计经验推导当前等级 (取阈值 <= experience 的最高等级)。"""
    current = UserLevel.L0
    for level, threshold in sorted(
        LEVEL_THRESHOLDS.items(), key=lambda kv: kv[1]
    ):
        if experience >= threshold:
            current = level
        else:
            break
    return current


def next_level(level: UserLevel) -> UserLevel | None:
    """下一等级; 已是最高级返回 None。"""
    nxt = level + 1
    if nxt in UserLevel.__members__.values() and nxt <= max(UserLevel):
        return UserLevel(nxt)
    return None


def experience_to_next_level(experience: int) -> int | None:
    """距离下一等级还差多少经验; 已满级返回 None。"""
    current = level_for_experience(experience)
    nxt = next_level(current)
    if nxt is None:
        return None
    return max(0, LEVEL_THRESHOLDS[nxt] - experience)

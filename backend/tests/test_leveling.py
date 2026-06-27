"""等级成长纯逻辑单元测试。"""

from __future__ import annotations

from backend.app.models.user import UserLevel
from backend.app.services.leveling import (
    experience_to_next_level,
    level_for_experience,
    next_level,
)


def test_level_for_experience_thresholds():
    assert level_for_experience(0) == UserLevel.L0
    assert level_for_experience(99) == UserLevel.L0
    assert level_for_experience(100) == UserLevel.L1
    assert level_for_experience(299) == UserLevel.L1
    assert level_for_experience(300) == UserLevel.L2
    assert level_for_experience(699) == UserLevel.L2
    assert level_for_experience(700) == UserLevel.L3
    assert level_for_experience(10_000) == UserLevel.L3


def test_next_level():
    assert next_level(UserLevel.L0) == UserLevel.L1
    assert next_level(UserLevel.L2) == UserLevel.L3
    assert next_level(UserLevel.L3) is None


def test_experience_to_next_level():
    assert experience_to_next_level(0) == 100
    assert experience_to_next_level(100) == 200  # L1, 距 L2(300) 还差 200
    assert experience_to_next_level(250) == 50
    assert experience_to_next_level(700) is None  # 满级

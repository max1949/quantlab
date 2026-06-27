"""engine.scoring 纯函数测试。"""

from __future__ import annotations

import pytest

from engine.scoring import WEIGHTS, apply_decay, research_score


def _validation(oos_sharpe, max_dd, wf_pos, sens_pos, last_sharpe):
    return {
        "oos": {"out_of_sample": {"sharpe": oos_sharpe, "max_drawdown": max_dd}},
        "walk_forward": {
            "summary": {"positive_ratio": wf_pos},
            "folds": [{"sharpe": 0.1}, {"sharpe": last_sharpe}],
        },
        "sensitivity": {"summary": {"positive_ratio": sens_pos}},
    }


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_apply_decay_bounds():
    assert apply_decay(80, 10.0) == pytest.approx(1.0, abs=1e-6)   # 近期很好 -> 上限
    assert apply_decay(80, -10.0) == pytest.approx(0.4, abs=1e-6)  # 近期很差 -> 下限
    assert 0.4 <= apply_decay(80, 0.0) <= 1.0


def test_strong_factor_high_score():
    v = _validation(oos_sharpe=2.0, max_dd=-0.05, wf_pos=1.0, sens_pos=1.0, last_sharpe=2.0)
    r = research_score(v)
    assert r["base_score"] > 90
    assert r["decay_factor"] > 0.9
    assert r["final_score"] > 85
    assert set(r["dimensions"]) == set(WEIGHTS)


def test_weak_factor_low_score():
    v = _validation(oos_sharpe=-1.0, max_dd=-0.6, wf_pos=0.0, sens_pos=0.0, last_sharpe=-5.0)
    r = research_score(v)
    assert r["base_score"] < 15  # 仅研究质量维度有分
    assert r["decay_factor"] == pytest.approx(0.4, abs=1e-3)  # 近期极差 -> 触底
    assert r["final_score"] < r["base_score"]


def test_decay_reduces_score_when_recent_bad():
    good_recent = research_score(
        _validation(1.0, -0.1, 0.75, 0.8, last_sharpe=1.5)
    )
    bad_recent = research_score(
        _validation(1.0, -0.1, 0.75, 0.8, last_sharpe=-1.5)
    )
    # 基础分相同, 近期差 -> 最终分更低
    assert good_recent["base_score"] == bad_recent["base_score"]
    assert bad_recent["final_score"] < good_recent["final_score"]


def test_quality_dimension_partial_when_incomplete():
    v = {"oos": {"out_of_sample": {"sharpe": 1.0, "max_drawdown": -0.1}}}
    r = research_score(v)
    assert r["dimensions"]["quality"] == pytest.approx(1 / 3, abs=1e-3)

"""engine.walk_forward 纯函数测试。"""

from __future__ import annotations

import pytest

from engine.cost_model import CostConfig
from engine.factor_engine import compute_template_factor, sample_price_frame
from engine.walk_forward import (
    evaluate_oos,
    holdout_split,
    robustness_score,
    sensitivity,
    walk_forward,
)


@pytest.fixture()
def ohlcv():
    return sample_price_frame(n=400, seed=21)


def _signal(df):
    return compute_template_factor(df, "momentum", {"window": 10})


def test_holdout_split_ratio(ohlcv):
    is_df, oos_df = holdout_split(ohlcv, 0.25)
    assert is_df.shape[0] + oos_df.shape[0] == ohlcv.shape[0]
    assert oos_df.shape[0] == pytest.approx(ohlcv.shape[0] * 0.25, abs=1)
    # 时间不重叠且有序
    assert is_df.index.max() < oos_df.index.min()


def test_holdout_bad_ratio(ohlcv):
    with pytest.raises(ValueError):
        holdout_split(ohlcv, 1.5)


def test_evaluate_oos_structure(ohlcv):
    out = evaluate_oos(_signal, ohlcv, CostConfig(), 0.3)
    assert set(out) >= {"in_sample", "out_of_sample", "sharpe_degradation", "oos_ratio"}
    assert "sharpe" in out["out_of_sample"]


def test_walk_forward_folds(ohlcv):
    out = walk_forward(_signal, ohlcv, CostConfig(), n_splits=4)
    assert len(out["folds"]) == 4
    assert 0.0 <= out["summary"]["positive_ratio"] <= 1.0
    assert out["summary"]["n_splits"] == 4


def test_walk_forward_min_splits(ohlcv):
    with pytest.raises(ValueError):
        walk_forward(_signal, ohlcv, n_splits=1)


def test_sensitivity_varies_params(ohlcv):
    variants = [
        (f"window={w}", (lambda df, w=w: compute_template_factor(df, "momentum", {"window": w})))
        for w in (5, 10, 20, 40)
    ]
    out = sensitivity(variants, ohlcv, CostConfig())
    assert len(out["points"]) == 4
    assert out["summary"]["n_variants"] == 4
    assert "min_sharpe" in out["summary"]


def test_robustness_score_bounds_and_grade():
    oos = {"out_of_sample": {"sharpe": 1.5}, "sharpe_degradation": 0.0}
    wf = {"summary": {"positive_ratio": 1.0, "n_splits": 4}}
    sens = {"summary": {"positive_ratio": 1.0, "n_variants": 4}}
    r = robustness_score(oos, wf, sens)
    assert r["score"] == 100.0
    assert r["grade"] == "稳健"


def test_robustness_score_weak_for_negative_oos():
    oos = {"out_of_sample": {"sharpe": -1.0}, "sharpe_degradation": 2.0}
    wf = {"summary": {"positive_ratio": 0.0, "n_splits": 4}}
    sens = {"summary": {"positive_ratio": 0.0, "n_variants": 4}}
    r = robustness_score(oos, wf, sens)
    assert r["score"] == 0.0
    assert r["grade"] == "脆弱"
    assert any("过拟合" in n for n in r["notes"])

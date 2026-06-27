"""engine.factor_engine 纯函数单元测试。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.factor_engine import (
    TEMPLATES,
    FactorError,
    compute_factor_stack,
    compute_template_factor,
    sample_price_frame,
    standardize,
    summarize,
    validate_template_params,
)


@pytest.fixture()
def df() -> pd.DataFrame:
    return sample_price_frame(n=120, seed=7)


def test_sample_frame_is_deterministic():
    a = sample_price_frame(n=50, seed=1)
    b = sample_price_frame(n=50, seed=1)
    pd.testing.assert_frame_equal(a, b)
    assert list(a.columns) == ["close", "volume"]
    assert a.shape[0] == 50


@pytest.mark.parametrize("code", list(TEMPLATES.keys()))
def test_each_template_outputs_aligned_series(df, code):
    s = compute_template_factor(df, code, {})
    assert isinstance(s, pd.Series)
    assert s.index.equals(df.index)
    assert s.name == code


def test_rsi_bounded_0_100(df):
    s = compute_template_factor(df, "rsi", {"window": 14}).dropna()
    assert (s >= 0).all() and (s <= 100).all()


def test_unknown_template_raises(df):
    with pytest.raises(FactorError):
        compute_template_factor(df, "does_not_exist", {})


def test_param_validation_bounds():
    with pytest.raises(FactorError):
        validate_template_params("momentum", {"window": 0})  # < min
    clean = validate_template_params("momentum", {"window": "30"})
    assert clean == {"window": 30}
    # 缺省补默认
    assert validate_template_params("rsi", {}) == {"window": 14}


def test_missing_required_column_raises():
    bad = pd.DataFrame({"volume": [1, 2, 3]})
    with pytest.raises(FactorError):
        compute_template_factor(bad, "momentum", {})


def test_standardize_zero_mean_unit_std():
    s = pd.Series(np.arange(100, dtype=float))
    z = standardize(s)
    assert abs(z.mean()) < 1e-9
    assert abs(z.std() - 1.0) < 1e-6


def test_standardize_constant_series_is_zero():
    s = pd.Series([5.0] * 10)
    assert (standardize(s) == 0).all()


def test_factor_stack_weighted_combination(df):
    mom = compute_template_factor(df, "momentum", {"window": 10})
    vol = compute_template_factor(df, "volatility", {"window": 10})
    stack = compute_factor_stack([(mom, 0.5), (vol, 0.5)])
    assert stack.index.equals(df.index)
    assert stack.name == "stack"
    # 与手工归一化组合一致
    expected = standardize(mom).fillna(0.0) * 0.5 + standardize(vol).fillna(0.0) * 0.5
    pd.testing.assert_series_equal(stack, expected, check_names=False)


def test_factor_stack_empty_raises():
    with pytest.raises(FactorError):
        compute_factor_stack([])


def test_factor_stack_zero_weights_raises(df):
    mom = compute_template_factor(df, "momentum", {})
    with pytest.raises(FactorError):
        compute_factor_stack([(mom, 0.0)])


def test_summarize_json_friendly(df):
    s = compute_template_factor(df, "momentum", {"window": 10})
    out = summarize(s)
    assert out["count"] == df.shape[0]
    assert out["valid_count"] <= out["count"]
    assert len(out["last"]) == 5
    assert set(out) >= {"mean", "std", "min", "max", "nan_ratio"}

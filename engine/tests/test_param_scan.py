"""因子扫描与 IC 指标测试。"""

from __future__ import annotations

from engine.factor_engine import compute_template_factor, sample_price_frame
from engine.factor_metrics import composite_factor_score, factor_ic
from engine.param_scan import build_param_grid, build_random_param_grid, scan_template_grid


def test_factor_ic_and_composite_score():
    df = sample_price_frame(300)
    sig = compute_template_factor(df, "momentum", {"window": 20})
    ic = factor_ic(sig, df["close"])
    assert ic["n_obs"] > 50
    assert isinstance(ic.get("ic_series"), list)
    score = composite_factor_score(
        sharpe=1.2, oos_sharpe=0.8, ic_mean=ic.get("ic_mean"), turnover=12.0
    )
    assert score is not None
    assert 0 <= score <= 100


def test_random_param_grid():
    grid = build_random_param_grid("momentum", n_trials=8)
    assert len(grid) == 8
    assert all("window" in g for g in grid)


def test_stack_weight_grid_scan():
    from engine.factor_engine import compute_template_factor, sample_price_frame
    from engine.param_scan import build_stack_weight_grid, scan_stack_weights

    df = sample_price_frame(400)

    def mom(df_in):
        return compute_template_factor(df_in, "momentum", {"window": 15})

    def rsi(df_in):
        return compute_template_factor(df_in, "rsi", {"window": 14})

    grid = build_stack_weight_grid(6)
    assert len(grid) == 6
    results = scan_stack_weights(
        df,
        [("mom", mom), ("rsi", rsi)],
        weight_grid=grid,
        factor_ids=["a", "b"],
    )
    assert len(results) == 6
    assert results[0]["rank"] == 1
    assert results[0]["params"]["weights"][0]["weight"] is not None


def test_param_grid_scan_ranks():
    df = sample_price_frame(400)
    grid = build_param_grid("momentum", steps=6)
    assert len(grid) >= 4
    results = scan_template_grid(df, "momentum", param_grid=grid[:6])
    assert len(results) == 6
    assert results[0]["rank"] == 1
    assert results[0].get("score") is not None or results[0]["metrics"]["sharpe"] is not None

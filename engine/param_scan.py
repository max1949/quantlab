"""模板因子参数网格扫描 — 纯函数。"""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from engine import factor_engine as fe
from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.factor_metrics import composite_factor_score, factor_ic
from engine.walk_forward import evaluate_oos

SignalFn = Callable[[pd.DataFrame], pd.Series]

MAX_VARIANTS = 24


def _grid_values(spec: fe.ParamSpec, steps: int = 8) -> list[int]:
    import numpy as np

    lo, hi = spec.min, spec.max
    if hi - lo <= steps:
        return list(range(lo, hi + 1))
    raw = [int(round(x)) for x in np.linspace(lo, hi, num=min(steps, hi - lo + 1))]
    return sorted(set(max(spec.min, min(spec.max, v)) for v in raw))


def build_param_grid(template_type: str, steps: int = 8) -> list[dict[str, int]]:
    tpl = fe.TEMPLATES.get(template_type)
    if tpl is None:
        raise fe.FactorError(f"未知模板: {template_type}")
    if len(tpl.params) == 1:
        spec = tpl.params[0]
        return [{spec.name: v} for v in _grid_values(spec, steps)][:MAX_VARIANTS]
    grids: list[dict[str, int]] = []
    vals = [_grid_values(p, max(4, steps // 2)) for p in tpl.params]
    for a in vals[0]:
        row = {tpl.params[0].name: a}
        if len(tpl.params) > 1:
            for b in vals[1]:
                grids.append({**row, tpl.params[1].name: b})
                if len(grids) >= MAX_VARIANTS:
                    return grids
        else:
            grids.append(row)
        if len(grids) >= MAX_VARIANTS:
            break
    return grids[:MAX_VARIANTS]


def build_random_param_grid(
    template_type: str,
    n_trials: int = 12,
    *,
    seed: int = 42,
) -> list[dict[str, int]]:
    """随机采样参数组合 (避免规则网格过拟合于步长)。"""
    import numpy as np

    tpl = fe.TEMPLATES.get(template_type)
    if tpl is None:
        raise fe.FactorError(f"未知模板: {template_type}")
    rng = np.random.default_rng(seed)
    cap = max(4, min(int(n_trials), MAX_VARIANTS))
    seen: set[tuple[tuple[str, int], ...]] = set()
    grid: list[dict[str, int]] = []
    attempts = 0
    while len(grid) < cap and attempts < cap * 20:
        attempts += 1
        row: dict[str, int] = {}
        for spec in tpl.params:
            row[spec.name] = int(rng.integers(spec.min, spec.max + 1))
        key = tuple(sorted(row.items()))
        if key in seen:
            continue
        seen.add(key)
        grid.append(row)
    return grid


def _signal_fn(template_type: str, params: dict) -> SignalFn:
    clean = fe.validate_template_params(template_type, params)

    def compute(df: pd.DataFrame) -> pd.Series:
        return fe.compute_template_factor(df, template_type, clean)

    return compute


def scan_template_grid(
    ohlcv: pd.DataFrame,
    template_type: str,
    *,
    param_grid: list[dict[str, int]] | None = None,
    cost_config: CostConfig | None = None,
    oos_ratio: float = 0.3,
    ic_horizon: int = 1,
    steps: int = 8,
) -> list[dict[str, Any]]:
    """对一组参数做快速回测 + OOS + IC, 返回可排序的结果列表。"""
    if "close" not in ohlcv.columns:
        raise ValueError("行情缺少 close")
    cfg = cost_config or CostConfig()
    grid = (param_grid or build_param_grid(template_type, steps=steps))[:MAX_VARIANTS]
    close = ohlcv["close"]
    results: list[dict[str, Any]] = []

    for params in grid:
        clean = fe.validate_template_params(template_type, params)
        signal_fn = _signal_fn(template_type, clean)
        full_signal = signal_fn(ohlcv)
        bt = run_backtest(full_signal, ohlcv, cfg)
        metrics = bt["metrics"]
        oos = evaluate_oos(signal_fn, ohlcv, cfg, oos_ratio=oos_ratio)
        ic = factor_ic(full_signal, close, horizon=ic_horizon)
        oos_sharpe = (oos.get("out_of_sample") or {}).get("sharpe")
        score = composite_factor_score(
            sharpe=metrics.get("sharpe"),
            oos_sharpe=oos_sharpe,
            ic_mean=ic.get("ic_mean"),
            turnover=metrics.get("turnover"),
        )
        results.append(
            {
                "params": clean,
                "label": ",".join(f"{k}={v}" for k, v in clean.items()),
                "metrics": metrics,
                "oos_sharpe": oos_sharpe,
                "oos_degradation": oos.get("sharpe_degradation"),
                "ic": ic,
                "score": score,
            }
        )

    results.sort(key=lambda r: (r.get("score") is None, -(r.get("score") or 0)))
    for i, row in enumerate(results):
        row["rank"] = i + 1
    return results


def build_stack_weight_grid(steps: int = 8) -> list[list[float]]:
    """两因子组合权重网格 — w0 从 0.15 到 0.85, w1 = 1 - w0。"""
    import numpy as np

    cap = max(2, min(int(steps), MAX_VARIANTS))
    w0_vals = np.linspace(0.15, 0.85, num=cap)
    return [[round(float(w0), 3), round(1.0 - float(w0), 3)] for w0 in w0_vals]


def scan_stack_weights(
    ohlcv: pd.DataFrame,
    components: list[tuple[str, SignalFn]],
    *,
    weight_grid: list[list[float]] | None = None,
    cost_config: CostConfig | None = None,
    oos_ratio: float = 0.3,
    ic_horizon: int = 1,
    steps: int = 8,
    factor_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """对两个因子做权重网格扫描 (标准化后线性组合)。"""
    if "close" not in ohlcv.columns:
        raise ValueError("行情缺少 close")
    if len(components) < 2:
        raise ValueError("组合扫描至少需要 2 个因子")
    cfg = cost_config or CostConfig()
    grid = (weight_grid or build_stack_weight_grid(steps))[:MAX_VARIANTS]
    close = ohlcv["close"]
    labels = [name for name, _ in components]
    fns = [fn for _, fn in components]
    ids = factor_ids or [str(i) for i in range(len(components))]
    results: list[dict[str, Any]] = []

    for weights in grid:
        w0, w1 = weights[0], weights[1]

        def stack_signal(df: pd.DataFrame, _w0=w0, _w1=w1) -> pd.Series:
            items = [(fn(df), w) for fn, w in zip(fns, (_w0, _w1))]
            return fe.compute_factor_stack(items)

        full_signal = stack_signal(ohlcv)
        bt = run_backtest(full_signal, ohlcv, cfg)
        metrics = bt["metrics"]
        oos = evaluate_oos(stack_signal, ohlcv, cfg, oos_ratio=oos_ratio)
        ic = factor_ic(full_signal, close, horizon=ic_horizon)
        oos_sharpe = (oos.get("out_of_sample") or {}).get("sharpe")
        score = composite_factor_score(
            sharpe=metrics.get("sharpe"),
            oos_sharpe=oos_sharpe,
            ic_mean=ic.get("ic_mean"),
            turnover=metrics.get("turnover"),
        )
        weight_params = [
            {"factor_id": ids[0], "weight": w0},
            {"factor_id": ids[1], "weight": w1},
        ]
        label = f"{w0:.0%}×{labels[0]} + {w1:.0%}×{labels[1]}"
        results.append(
            {
                "params": {"weights": weight_params},
                "label": label,
                "metrics": metrics,
                "oos_sharpe": oos_sharpe,
                "oos_degradation": oos.get("sharpe_degradation"),
                "ic": ic,
                "score": score,
            }
        )

    results.sort(key=lambda r: (r.get("score") is None, -(r.get("score") or 0)))
    for i, row in enumerate(results):
        row["rank"] = i + 1
    return results


def _params_key(params: dict) -> str:
    return ",".join(f"{k}={v}" for k, v in sorted(params.items()))


def scan_template_multi_symbol(
    ohlcv_map: dict[str, pd.DataFrame],
    template_type: str,
    *,
    param_grid: list[dict[str, int]] | None = None,
    cost_config: CostConfig | None = None,
    oos_ratio: float = 0.3,
    ic_horizon: int = 1,
    steps: int = 8,
) -> list[dict[str, Any]]:
    """多标的同一参数网格 — 按跨标的平均综合分排序。"""
    if not ohlcv_map:
        raise ValueError("至少需要一个标的")
    if len(ohlcv_map) > 3:
        raise ValueError("最多同时扫描 3 个标的")

    grid = (param_grid or build_param_grid(template_type, steps=steps))[:MAX_VARIANTS]
    per_symbol: dict[str, list[dict[str, Any]]] = {}
    for sym, df in ohlcv_map.items():
        per_symbol[sym] = scan_template_grid(
            df,
            template_type,
            param_grid=grid,
            cost_config=cost_config,
            oos_ratio=oos_ratio,
            ic_horizon=ic_horizon,
            steps=steps,
        )

    merged: dict[str, dict[str, Any]] = {}
    for sym, rows in per_symbol.items():
        for row in rows:
            key = _params_key(row.get("params") or {})
            if key not in merged:
                merged[key] = {
                    "params": row.get("params") or {},
                    "label": row.get("label") or key,
                    "per_symbol": {},
                    "template_row": row,
                }
            merged[key]["per_symbol"][sym] = {
                "score": row.get("score"),
                "oos_sharpe": row.get("oos_sharpe"),
                "sharpe": (row.get("metrics") or {}).get("sharpe"),
                "ic_mean": (row.get("ic") or {}).get("ic_mean"),
                "turnover": (row.get("metrics") or {}).get("turnover"),
            }

    results: list[dict[str, Any]] = []
    for entry in merged.values():
        breakdown = entry["per_symbol"]
        scores = [v["score"] for v in breakdown.values() if v.get("score") is not None]
        oos_vals = [v["oos_sharpe"] for v in breakdown.values() if v.get("oos_sharpe") is not None]
        ic_vals = [v["ic_mean"] for v in breakdown.values() if v.get("ic_mean") is not None]
        turn_vals = [v["turnover"] for v in breakdown.values() if v.get("turnover") is not None]
        avg_score = sum(scores) / len(scores) if scores else None
        avg_oos = sum(oos_vals) / len(oos_vals) if oos_vals else None
        base = dict(entry["template_row"])
        base["score"] = round(avg_score, 1) if avg_score is not None else None
        base["oos_sharpe"] = avg_oos
        if ic_vals:
            base["ic"] = {**(base.get("ic") or {}), "ic_mean": sum(ic_vals) / len(ic_vals)}
        if turn_vals and base.get("metrics"):
            base["metrics"] = {
                **base["metrics"],
                "turnover": sum(turn_vals) / len(turn_vals),
            }
        base["symbol_breakdown"] = breakdown
        base["multi_symbol"] = True
        results.append(base)

    results.sort(key=lambda r: (r.get("score") is None, -(r.get("score") or 0)))
    for i, row in enumerate(results):
        row["rank"] = i + 1
    return results

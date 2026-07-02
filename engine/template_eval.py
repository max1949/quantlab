"""模板因子快速评估 — 在真实行情上评估单组参数。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from engine import factor_engine as fe
from engine.signal_eval import evaluate_signal


def evaluate_template(
    ohlcv: pd.DataFrame,
    template_type: str,
    params: dict,
    *,
    oos_ratio: float = 0.3,
    ic_horizon: int | None = None,
    timeframe: str = "1d",
) -> dict[str, Any]:
    clean = fe.validate_template_params(template_type, params)
    label = ",".join(f"{k}={v}" for k, v in clean.items())

    def signal_fn(df: pd.DataFrame) -> pd.Series:
        return fe.compute_template_factor(df, template_type, clean)

    result = evaluate_signal(
        ohlcv,
        signal_fn,
        label=label,
        kind="template",
        oos_ratio=oos_ratio,
        ic_horizon=ic_horizon,
        timeframe=timeframe,
    )
    result["template_type"] = template_type
    result["params"] = clean
    result["label"] = label
    return result

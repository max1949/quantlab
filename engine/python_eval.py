"""Python 因子快速评估 — 沙箱执行 compute(ohlcv) 后跑回测 + OOS + IC。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from engine.signal_eval import evaluate_signal
from sandbox.runner import SandboxError, run_user_factor


def evaluate_python_source(
    ohlcv: pd.DataFrame,
    source: str,
    *,
    oos_ratio: float = 0.3,
    ic_horizon: int | None = None,
    timeframe: str = "1d",
) -> dict[str, Any]:
    src = source.strip()
    if not src:
        raise SandboxError("源码为空")

    def signal_fn(df: pd.DataFrame) -> pd.Series:
        return run_user_factor(src, df)

    result = evaluate_signal(
        ohlcv,
        signal_fn,
        label="compute(ohlcv)",
        kind="python",
        oos_ratio=oos_ratio,
        ic_horizon=ic_horizon,
        timeframe=timeframe,
    )
    result["source"] = src
    return result

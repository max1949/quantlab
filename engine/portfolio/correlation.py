"""Strategy return correlation utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def pairwise_return_correlation(
    returns: dict[str, pd.Series],
) -> dict[str, Any]:
    """Compute pairwise Pearson correlation on aligned returns."""
    if len(returns) < 2:
        return {"matrix": {}, "pairs": [], "max_abs": 0.0}
    df = pd.DataFrame({k: v.astype(float) for k, v in returns.items()}).dropna(how="any")
    if df.shape[0] < 3:
        return {"matrix": {}, "pairs": [], "max_abs": 0.0, "insufficient": True}
    corr = df.corr()
    pairs: list[dict[str, Any]] = []
    cols = list(corr.columns)
    max_abs = 0.0
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            v = float(corr.loc[a, b])
            if np.isnan(v):
                continue
            max_abs = max(max_abs, abs(v))
            pairs.append({"a": a, "b": b, "corr": v})
    matrix = {c: {r: float(corr.loc[c, r]) for r in cols} for c in cols}
    return {"matrix": matrix, "pairs": pairs, "max_abs": max_abs}

"""Factor / style exposure estimates for portfolio intelligence."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def style_exposure(
    returns: dict[str, pd.Series],
    *,
    market: pd.Series | None = None,
) -> dict[str, Any]:
    """Simple style betas: vol, skew proxy, and optional market beta."""
    out: dict[str, Any] = {}
    for sid, ser in returns.items():
        r = ser.astype(float).dropna()
        if r.empty:
            out[sid] = {"vol": None, "skew": None, "market_beta": None}
            continue
        vol = float(r.std())
        skew = float(((r - r.mean()) ** 3).mean() / (r.std() ** 3 + 1e-12))
        beta = None
        if market is not None:
            m = market.astype(float).reindex(r.index).dropna()
            rr = r.reindex(m.index).dropna()
            m = m.reindex(rr.index)
            if len(rr) >= 5 and float(m.std()) > 0:
                beta = float(np.cov(rr, m)[0, 1] / (float(m.var()) + 1e-12))
        out[sid] = {"vol": vol, "skew": skew, "market_beta": beta}
    return out

"""回测响应附带市场制度提示 + 制度×策略适配。"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.app.models.factor import Factor
from backend.app.models.user import User
from backend.app.services import market_data_policy as mdp


def _attach_strategy_fit(regime: dict | None, factor: Factor | None) -> dict | None:
    if regime is None:
        return None
    if factor is None:
        return regime
    from engine.regime_strategy import infer_strategy_style, score_regime_fit

    style = infer_strategy_style(
        kind=factor.kind, template_type=factor.template_type, name=factor.name
    )
    fit = score_regime_fit(regime["regime"], style)
    return {**regime, **fit}


def market_regime_for_symbol(
    db: Session,
    user: User,
    symbol: str,
    timeframe: str = "1d",
    *,
    factor: Factor | None = None,
) -> dict | None:
    try:
        from engine.regime import detect_vol_regime

        df = mdp.load_for_user(db, user, symbol, timeframe)
        regime = detect_vol_regime(df)
        return _attach_strategy_fit(regime, factor)
    except Exception:  # noqa: BLE001 — 制度提示为可选增强
        return None


def market_regime_for_factor(
    db: Session,
    user: User,
    factor_id: uuid.UUID,
    symbol: str,
    timeframe: str = "1d",
) -> dict | None:
    factor = db.get(Factor, factor_id)
    if factor is None:
        return None
    return market_regime_for_symbol(db, user, symbol, timeframe, factor=factor)

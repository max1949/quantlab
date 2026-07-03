"""回测响应附带市场制度提示。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services import market_data_policy as mdp


def market_regime_for_symbol(
    db: Session,
    user: User,
    symbol: str,
    timeframe: str = "1d",
) -> dict | None:
    try:
        from engine.regime import detect_vol_regime

        df = mdp.load_for_user(db, user, symbol, timeframe)
        return detect_vol_regime(df)
    except Exception:  # noqa: BLE001 — 制度提示为可选增强
        return None

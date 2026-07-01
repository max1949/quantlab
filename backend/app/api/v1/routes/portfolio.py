"""L4 组合优化 / 模拟实盘路由。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import require_feature
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.portfolio import (
    PaperSimulateCreate,
    PaperSimulateOut,
    PortfolioOptimizeCreate,
    PortfolioOptimizeOut,
)
from backend.app.services import market_data
from engine import portfolio as pf

router = APIRouter()


def _load_returns(db: Session, symbols: list[str]):
    closes = {}
    for sym in symbols:
        if market_data.get_dataset(db, sym) is None:
            raise FileNotFoundError(sym)
        closes[sym] = market_data.load_ohlcv(sym)["close"]
    return pf.returns_from_closes(closes)


@router.post(
    "/optimize",
    response_model=PortfolioOptimizeOut,
    summary="L4 组合优化 (需 L4 + 专业月卡)",
)
def optimize_portfolio(
    payload: PortfolioOptimizeCreate,
    current_user: Annotated[User, Depends(require_feature("portfolio_optimize"))],
    db: Annotated[Session, Depends(get_db)],
) -> PortfolioOptimizeOut:
    try:
        returns = _load_returns(db, payload.symbols)
        result = pf.optimize_weights(returns, payload.method)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"行情不存在: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return PortfolioOptimizeOut(symbols=payload.symbols, **result)


@router.post(
    "/paper-simulate",
    response_model=PaperSimulateOut,
    summary="L4 模拟实盘组合净值 (需 L4 + 专业月卡)",
)
def paper_simulate(
    payload: PaperSimulateCreate,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperSimulateOut:
    try:
        returns = _load_returns(db, payload.symbols)
        result = pf.simulate_portfolio(returns, payload.weights, payload.rebalance)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"行情不存在: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return PaperSimulateOut(
        symbols=payload.symbols,
        weights=payload.weights,
        **result,
    )

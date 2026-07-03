"""回测与行情数据集路由 (Sprint 4)。

回测重计算与 API 解耦: 创建后由 Celery worker 执行 (eager 模式下同步执行)。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser, require_feature
from backend.app.core.database import get_db
from backend.app.schemas.backtest import (
    BacktestCreate,
    BacktestDetail,
    BacktestSummary,
    CostSensitivityCreate,
    CostSensitivityOut,
    CrossSectionBacktestCreate,
    CrossSectionBacktestOut,
    DataQualityOut,
    DatasetOut,
)
from backend.app.models.user import User
from backend.app.services import backtest_service, factor_service, market_data
from backend.app.services import market_data_policy as mdp
from backend.app.services import rate_limit

router = APIRouter()


@router.get(
    "/datasets",
    response_model=list[DatasetOut],
    tags=["data"],
    summary="可用行情数据集",
)
def list_datasets(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[DatasetOut]:
    return [DatasetOut(**d) for d in mdp.list_datasets_for_user(db, current_user)]


@router.get(
    "/datasets/regime",
    tags=["data"],
    summary="波动率制度识别 (low/mid/high)",
)
def dataset_regime(
    symbol: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    timeframe: str = "1d",
) -> dict:
    from engine.regime import detect_vol_regime

    if market_data.get_dataset(db, symbol, timeframe) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行情数据集不存在",
        )
    try:
        df = mdp.load_for_user(db, current_user, symbol, timeframe)
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    try:
        out = detect_vol_regime(df)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return {"symbol": symbol.upper(), "timeframe": timeframe, **out}


@router.get(
    "/datasets/quality",
    response_model=DataQualityOut,
    tags=["data"],
    summary="行情数据质量评估",
)
def dataset_quality(
    symbol: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    timeframe: str = "1d",
) -> DataQualityOut:
    from engine.data_quality import assess_ohlcv_quality

    if market_data.get_dataset(db, symbol, timeframe) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行情数据集不存在",
        )
    try:
        df = mdp.load_for_user(db, current_user, symbol, timeframe)
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    report = assess_ohlcv_quality(df, timeframe)
    return DataQualityOut(symbol=symbol.upper(), timeframe=timeframe, **report)


@router.post(
    "/backtests",
    response_model=BacktestDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["backtest"],
    summary="创建并运行回测 (绑定数据快照 + 成本; 异步/Celery)",
)
def create_backtest(
    payload: BacktestCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BacktestDetail:
    try:
        rate_limit.check_backtest(str(current_user.id))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    try:
        bt = backtest_service.create_and_run(
            db,
            current_user,
            payload.factor_id,
            payload.symbol,
            {"fee_rate": payload.fee_rate, "slippage_bps": payload.slippage_bps},
            payload.timeframe,
        )
    except factor_service.FactorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在"
        )
    except backtest_service.DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行情数据集不存在 (先生成样本数据: scripts/seed-market-data.ps1)",
        )
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    detail = BacktestDetail.model_validate(bt)
    return detail.model_copy(update={"academy_rewards": getattr(bt, "academy_rewards", [])})


@router.post(
    "/backtests/cross-section",
    response_model=CrossSectionBacktestOut,
    status_code=status.HTTP_200_OK,
    tags=["backtest"],
    summary="L2 截面多标的回测 (需 L2 + 研究员会员)",
)
def cross_section_backtest(
    payload: CrossSectionBacktestCreate,
    current_user: Annotated[User, Depends(require_feature("backtest_cross_section"))],
    db: Annotated[Session, Depends(get_db)],
) -> CrossSectionBacktestOut:
    try:
        result = backtest_service.run_cross_section_analysis(
            db,
            current_user,
            payload.factor_id,
            payload.symbols,
            {"fee_rate": payload.fee_rate, "slippage_bps": payload.slippage_bps},
            top_n=payload.top_n,
            long_short=payload.long_short,
        )
    except factor_service.FactorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在"
        )
    except backtest_service.DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"行情数据集不存在: {exc}",
        )
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return CrossSectionBacktestOut(**result)


@router.post(
    "/backtests/cost-sensitivity",
    response_model=CostSensitivityOut,
    status_code=status.HTTP_200_OK,
    tags=["backtest"],
    summary="L2 成本敏感性分析 (需 L2 + 研究员会员)",
)
def cost_sensitivity(
    payload: CostSensitivityCreate,
    current_user: Annotated[User, Depends(require_feature("cost_sensitivity"))],
    db: Annotated[Session, Depends(get_db)],
) -> CostSensitivityOut:
    try:
        result = backtest_service.run_cost_sensitivity(
            db,
            current_user,
            payload.factor_id,
            payload.symbol,
            payload.fee_rates,
            payload.slippage_bps_values,
        )
    except factor_service.FactorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在"
        )
    except backtest_service.DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"行情数据集不存在: {exc}",
        )
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return CostSensitivityOut(**result)


@router.get(
    "/backtests",
    response_model=list[BacktestSummary],
    tags=["backtest"],
    summary="我的回测列表",
)
def list_backtests(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[BacktestSummary]:
    return [
        BacktestSummary.model_validate(b)
        for b in backtest_service.list_backtests(db, current_user.id)
    ]


@router.get(
    "/backtests/{backtest_id}",
    response_model=BacktestDetail,
    tags=["backtest"],
    summary="回测详情 (状态/指标/净值/研究报告)",
)
def get_backtest(
    backtest_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BacktestDetail:
    try:
        bt = backtest_service.get_backtest(
            db, current_user.id, uuid.UUID(backtest_id)
        )
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="回测不存在"
        )
    return BacktestDetail.model_validate(bt)

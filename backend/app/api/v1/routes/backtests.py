"""回测与行情数据集路由 (Sprint 4)。

回测重计算与 API 解耦: 创建后由 Celery worker 执行 (eager 模式下同步执行)。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.backtest import (
    BacktestCreate,
    BacktestDetail,
    BacktestSummary,
    DatasetOut,
)
from backend.app.services import backtest_service, factor_service, market_data

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
    return [DatasetOut.model_validate(d) for d in market_data.list_datasets(db)]


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
        bt = backtest_service.create_and_run(
            db,
            current_user,
            payload.factor_id,
            payload.symbol,
            {"fee_rate": payload.fee_rate, "slippage_bps": payload.slippage_bps},
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
    return BacktestDetail.model_validate(bt)


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

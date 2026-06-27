"""回测业务逻辑 (Sprint 4)。

职责: 绑定 (因子 + 数据快照 + 成本配置), 入队/执行, 落库指标与研究报告。
计算本身全在 engine (纯函数), 本模块不做数学, 只编排与持久化。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.report import build_research_report
from backend.app.core.config import get_settings
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.market import DataSnapshot
from backend.app.services import factor_service, market_data


class DatasetNotFoundError(Exception):
    pass


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def create_backtest(
    db: Session,
    owner,
    factor_id: uuid.UUID,
    symbol: str,
    cost_config: dict | None,
) -> Backtest:
    """创建回测 (pending) 并绑定数据快照。校验因子归属与数据集存在。"""
    factor = factor_service.get_factor(db, owner.id, factor_id)  # 可能抛 FactorNotFound

    if market_data.get_dataset(db, symbol) is None:
        raise DatasetNotFoundError(symbol)
    df = market_data.load_ohlcv(symbol)
    snapshot = market_data.create_snapshot(db, symbol, df)

    bt = Backtest(
        owner_id=owner.id,
        factor_id=factor.id,
        snapshot_id=snapshot.id,
        symbol=symbol,
        cost_config=cost_config or {},
        status=BacktestStatus.PENDING.value,
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)
    return bt


def execute(db: Session, backtest_id) -> Backtest | None:
    """执行回测计算 (供 Celery worker 或 eager 调用)。"""
    bt = db.get(Backtest, _as_uuid(backtest_id))
    if bt is None:
        return None

    bt.status = BacktestStatus.RUNNING.value
    db.commit()

    try:
        factor = db.get(factor_service.Factor, bt.factor_id)
        if factor is None:
            raise factor_service.FactorNotFoundError(str(bt.factor_id))

        ohlcv = market_data.load_ohlcv(bt.symbol)
        signal = factor_service._compute_series(db, bt.owner_id, factor, ohlcv)

        cfg = CostConfig(**(bt.cost_config or {}))
        result = run_backtest(signal, ohlcv, cfg)

        snap = db.get(DataSnapshot, bt.snapshot_id) if bt.snapshot_id else None
        snap_dict = (
            {
                "symbol": snap.symbol,
                "start_date": snap.start_date.isoformat(),
                "end_date": snap.end_date.isoformat(),
                "rows": snap.rows,
                "content_hash": snap.content_hash,
            }
            if snap
            else None
        )

        report = build_research_report(
            factor_name=factor.name,
            factor_kind=factor.kind,
            factor_spec=factor.spec,
            symbol=bt.symbol,
            cost_config={
                "fee_rate": cfg.fee_rate,
                "slippage_bps": cfg.slippage_bps,
            },
            metrics=result["metrics"],
            snapshot=snap_dict,
        )

        bt.metrics = result["metrics"]
        bt.equity_curve = result["equity_curve"]
        bt.report = report
        bt.status = BacktestStatus.SUCCESS.value
        bt.error = None
    except Exception as exc:  # noqa: BLE001 - 落库失败原因, 不让 worker 崩
        bt.status = BacktestStatus.FAILED.value
        bt.error = f"{type(exc).__name__}: {exc}"
    finally:
        bt.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(bt)
    return bt


def create_and_run(
    db: Session, owner, factor_id: uuid.UUID, symbol: str, cost_config: dict | None
) -> Backtest:
    """创建回测并触发执行。

    - eager 模式 (测试/无 worker): 同步执行, 复用当前会话, 响应即含结果。
    - 否则: 派发到 Celery worker (重计算与 API 解耦), 响应为 pending。
    """
    bt = create_backtest(db, owner, factor_id, symbol, cost_config)
    if get_settings().celery_task_always_eager:
        execute(db, bt.id)
        db.refresh(bt)
    else:
        from backend.app.tasks.backtest_tasks import run_backtest_task

        run_backtest_task.delay(str(bt.id))
    return bt


def list_backtests(db: Session, owner_id: uuid.UUID) -> list[Backtest]:
    return list(
        db.execute(
            select(Backtest)
            .where(Backtest.owner_id == owner_id)
            .order_by(Backtest.created_at.desc())
        )
        .scalars()
        .all()
    )


def get_backtest(db: Session, owner_id: uuid.UUID, backtest_id: uuid.UUID) -> Backtest:
    bt = db.get(Backtest, backtest_id)
    if bt is None or bt.owner_id != owner_id:
        raise FileNotFoundError(str(backtest_id))
    return bt

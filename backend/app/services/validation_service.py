"""科学验证业务逻辑 (Sprint 5)。

编排 engine.walk_forward 的纯函数: 构造在任意数据切片上计算因子信号的闭包
(template / stack 都支持), 跑 OOS / Walk-Forward / 敏感性, 汇总稳健性评分。
重计算异步执行 (Celery), 与回测同构。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import factor_engine as fe
from engine import walk_forward as wf
from engine.cost_model import CostConfig
from backend.app.core.config import get_settings
from backend.app.models.factor import Factor, FactorKind
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.services import factor_service, market_data
from backend.app.services.backtest_service import DatasetNotFoundError


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _signal_fn(db: Session, owner_id: uuid.UUID, factor: Factor):
    """构造 compute_signal(df)->Series 闭包 (在给定切片上独立算信号, 避免泄漏)。"""

    def fn(df: pd.DataFrame) -> pd.Series:
        return factor_service._compute_series(db, owner_id, factor, df)

    return fn


def _sensitivity_variants(factor: Factor, db: Session, owner_id: uuid.UUID):
    """敏感性变体: 模板因子扰动其窗口参数; 组合器仅基准一项 (退化)。"""
    if factor.kind == FactorKind.TEMPLATE.value:
        tpl = fe.TEMPLATES.get(factor.template_type)
        if tpl and tpl.params:
            spec = tpl.params[0]
            base = int(factor.spec.get("params", {}).get(spec.name, spec.default))
            values = sorted(
                {
                    max(spec.min, min(spec.max, int(round(base * m))))
                    for m in (0.5, 0.75, 1.0, 1.25, 1.5)
                }
            )
            ftype = factor.template_type
            return [
                (
                    f"{spec.name}={v}",
                    (lambda df, v=v: fe.compute_template_factor(df, ftype, {spec.name: v})),
                )
                for v in values
            ]
    # 组合器: 无单一参数可扫, 用基准信号作单点 (稳健性回退到 WF 一致性)
    return [("base", _signal_fn(db, owner_id, factor))]


def create_validation(
    db: Session,
    owner,
    factor_id: uuid.UUID,
    symbol: str,
    cost_config: dict | None,
    oos_ratio: float,
    n_splits: int,
) -> Validation:
    factor = factor_service.get_factor(db, owner.id, factor_id)  # 可能抛 FactorNotFound
    if market_data.get_dataset(db, symbol) is None:
        raise DatasetNotFoundError(symbol)
    df = market_data.load_ohlcv(symbol)
    snapshot = market_data.create_snapshot(db, symbol, df)

    v = Validation(
        owner_id=owner.id,
        factor_id=factor.id,
        snapshot_id=snapshot.id,
        symbol=symbol,
        cost_config=cost_config or {},
        oos_ratio=oos_ratio,
        n_splits=n_splits,
        status=ValidationStatus.PENDING.value,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def execute(db: Session, validation_id) -> Validation | None:
    v = db.get(Validation, _as_uuid(validation_id))
    if v is None:
        return None

    v.status = ValidationStatus.RUNNING.value
    db.commit()

    try:
        factor = db.get(Factor, v.factor_id)
        if factor is None:
            raise factor_service.FactorNotFoundError(str(v.factor_id))

        ohlcv = market_data.load_ohlcv(v.symbol)
        cfg = CostConfig(**(v.cost_config or {}))
        signal_fn = _signal_fn(db, v.owner_id, factor)

        oos = wf.evaluate_oos(signal_fn, ohlcv, cfg, v.oos_ratio)
        walk = wf.walk_forward(signal_fn, ohlcv, cfg, v.n_splits)
        variants = _sensitivity_variants(factor, db, v.owner_id)
        sens = wf.sensitivity(variants, ohlcv, cfg)
        robustness = wf.robustness_score(oos, walk, sens)

        v.oos = oos
        v.walk_forward = walk
        v.sensitivity = sens
        v.robustness = robustness
        v.status = ValidationStatus.SUCCESS.value
        v.error = None
    except Exception as exc:  # noqa: BLE001
        v.status = ValidationStatus.FAILED.value
        v.error = f"{type(exc).__name__}: {exc}"
    finally:
        v.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(v)
    return v


def create_and_run(
    db: Session,
    owner,
    factor_id: uuid.UUID,
    symbol: str,
    cost_config: dict | None,
    oos_ratio: float,
    n_splits: int,
) -> Validation:
    v = create_validation(
        db, owner, factor_id, symbol, cost_config, oos_ratio, n_splits
    )
    if get_settings().celery_task_always_eager:
        execute(db, v.id)
        db.refresh(v)
    else:
        from backend.app.tasks.validation_tasks import run_validation_task

        run_validation_task.delay(str(v.id))
    return v


def list_validations(db: Session, owner_id: uuid.UUID) -> list[Validation]:
    return list(
        db.execute(
            select(Validation)
            .where(Validation.owner_id == owner_id)
            .order_by(Validation.created_at.desc())
        )
        .scalars()
        .all()
    )


def get_validation(db: Session, owner_id: uuid.UUID, validation_id: uuid.UUID) -> Validation:
    v = db.get(Validation, validation_id)
    if v is None or v.owner_id != owner_id:
        raise FileNotFoundError(str(validation_id))
    return v

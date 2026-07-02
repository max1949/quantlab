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
from engine import advanced_research as ar
from engine import walk_forward as wf
from engine.cost_model import CostConfig
from engine.factor_metrics import IC_HORIZON_BY_TF, factor_ic
from backend.app.core.config import get_settings
from backend.app.models.factor import Factor, FactorKind
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.models.market import DataSnapshot
from backend.app.services import factor_service, market_data
from backend.app.services import market_data_policy as mdp
from backend.app.services.backtest_service import DatasetNotFoundError
from backend.app.models.user import User


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
    timeframe: str = "1d",
) -> Validation:
    factor = factor_service.get_factor(db, owner.id, factor_id)  # 可能抛 FactorNotFound
    if market_data.get_dataset(db, symbol, timeframe) is None:
        raise DatasetNotFoundError(symbol)
    df = mdp.load_for_user(db, owner, symbol, timeframe)
    snapshot = market_data.create_snapshot(db, symbol, df, timeframe)

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

        snap = db.get(DataSnapshot, v.snapshot_id) if v.snapshot_id else None
        tf = snap.timeframe if snap else "1d"
        owner = db.get(User, v.owner_id)
        if owner is None:
            raise factor_service.FactorNotFoundError(str(v.factor_id))
        ohlcv = mdp.load_for_snapshot(db, owner, v.symbol, snap)
        cfg = CostConfig(**(v.cost_config or {}))
        signal_fn = _signal_fn(db, v.owner_id, factor)

        from backend.app.core.config import get_settings

        settings = get_settings()
        holdout_ratio = settings.sealed_holdout_ratio
        n = ohlcv.shape[0]
        cut = int(n * (1.0 - holdout_ratio))
        dev_ohlcv = ohlcv.iloc[:cut] if cut >= 80 else ohlcv

        oos = wf.evaluate_oos(signal_fn, dev_ohlcv, cfg, v.oos_ratio)
        walk = wf.walk_forward(signal_fn, dev_ohlcv, cfg, v.n_splits)
        variants = _sensitivity_variants(factor, db, v.owner_id)
        sens = wf.sensitivity(variants, dev_ohlcv, cfg)
        sealed = wf.evaluate_sealed_holdout(signal_fn, ohlcv, cfg, holdout_ratio)
        robustness = wf.robustness_score(oos, walk, sens)
        robustness["sealed_holdout"] = sealed
        try:
            signal = signal_fn(dev_ohlcv)
            ic_horizon = IC_HORIZON_BY_TF.get(tf, 1)
            robustness["factor_ic"] = factor_ic(
                signal, dev_ohlcv["close"], horizon=ic_horizon
            )
        except Exception:
            robustness["factor_ic"] = {"ic_mean": None, "rank_ic_mean": None}

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
    # 验证成功后刷新研究信用分 (有效验证沉淀)。
    if v.status == ValidationStatus.SUCCESS.value:
        from backend.app.services import growth_service

        owner = db.get(User, v.owner_id)
        if owner is not None:
            growth_service.recompute_contribution_score(db, owner)
            from backend.app.services import academy_hooks

            v.academy_rewards = academy_hooks.on_validation_success(db, owner)
        try:
            from backend.app.services import paper_tracking_service as pts

            pts.record_snapshot(db, v.factor_id, v.owner_id)
        except Exception:
            pass  # 纸面跟踪失败不影响验证结果
    return v


def create_and_run(
    db: Session,
    owner,
    factor_id: uuid.UUID,
    symbol: str,
    cost_config: dict | None,
    oos_ratio: float,
    n_splits: int,
    timeframe: str = "1d",
) -> Validation:
    v = create_validation(
        db, owner, factor_id, symbol, cost_config, oos_ratio, n_splits, timeframe
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


def run_orthogonalize(
    db: Session,
    owner,
    target_factor_id: uuid.UUID,
    control_factor_ids: list[uuid.UUID],
    symbol: str,
) -> dict:
    """L3: 目标因子相对控制因子的正交化分析。"""
    target = factor_service.get_factor(db, owner.id, target_factor_id)
    controls = [factor_service.get_factor(db, owner.id, fid) for fid in control_factor_ids]
    if market_data.get_dataset(db, symbol) is None:
        raise DatasetNotFoundError(symbol)
    ohlcv = mdp.load_for_user(db, owner, symbol, "1d")
    target_signal = factor_service._compute_series(db, owner.id, target, ohlcv)
    control_signals = {
        f.name: factor_service._compute_series(db, owner.id, f, ohlcv)
        for f in controls
    }
    result = ar.orthogonalize(target_signal, control_signals)
    return {
        "target_factor_id": target.id,
        "target_factor_name": target.name,
        "control_factors": [{"id": f.id, "name": f.name} for f in controls],
        "symbol": symbol,
        "result": result,
    }


def run_robustness_test(
    db: Session,
    owner,
    factor_id: uuid.UUID,
    symbol: str,
    cost_config: dict | None = None,
) -> dict:
    """L3: 参数稳健性测试。"""
    factor = factor_service.get_factor(db, owner.id, factor_id)
    if market_data.get_dataset(db, symbol) is None:
        raise DatasetNotFoundError(symbol)
    ohlcv = mdp.load_for_user(db, owner, symbol, "1d")
    cfg = CostConfig(**(cost_config or {}))
    variants = _sensitivity_variants(factor, db, owner.id)
    sens = wf.sensitivity(variants, ohlcv, cfg)
    verdict = ar.robustness_verdict(sens["points"], sens["summary"])
    return {
        "factor_id": factor.id,
        "factor_name": factor.name,
        "symbol": symbol,
        "sensitivity": sens,
        "verdict": verdict,
    }


def run_overfit_check(
    db: Session,
    owner,
    factor_id: uuid.UUID,
    symbol: str,
    cost_config: dict | None = None,
    oos_ratio: float = 0.3,
    n_splits: int = 4,
) -> dict:
    """L3: 过拟合红旗检查。"""
    factor = factor_service.get_factor(db, owner.id, factor_id)
    if market_data.get_dataset(db, symbol) is None:
        raise DatasetNotFoundError(symbol)
    ohlcv = mdp.load_for_user(db, owner, symbol, "1d")
    cfg = CostConfig(**(cost_config or {}))
    signal_fn = _signal_fn(db, owner.id, factor)
    oos = wf.evaluate_oos(signal_fn, ohlcv, cfg, oos_ratio)
    walk = wf.walk_forward(signal_fn, ohlcv, cfg, n_splits)
    sens = wf.sensitivity(_sensitivity_variants(factor, db, owner.id), ohlcv, cfg)
    overfit = ar.overfit_check(oos, walk, sens)
    return {
        "factor_id": factor.id,
        "factor_name": factor.name,
        "symbol": symbol,
        "oos": oos,
        "walk_forward": walk,
        "sensitivity": sens,
        "overfit": overfit,
    }

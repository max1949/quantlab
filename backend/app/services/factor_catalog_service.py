"""因子资产库 — 聚合绩效元数据 + 项目内冗余度 (机构 Factor Intelligence 基础)。"""

from __future__ import annotations

import uuid

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.services import factor_service, market_data_policy as mdp
from engine import advanced_research as ar


def _latest_backtest(db: Session, factor_id: uuid.UUID) -> Backtest | None:
    return db.execute(
        select(Backtest)
        .where(Backtest.factor_id == factor_id, Backtest.status == BacktestStatus.SUCCESS.value)
        .order_by(Backtest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _latest_validation(db: Session, factor_id: uuid.UUID) -> Validation | None:
    return db.execute(
        select(Validation)
        .where(Validation.factor_id == factor_id, Validation.status == ValidationStatus.SUCCESS.value)
        .order_by(Validation.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _factor_series(
    db: Session, owner_id: uuid.UUID, factor: Factor, ohlcv: pd.DataFrame
) -> pd.Series | None:
    try:
        return factor_service.compute_factor_series(db, owner_id, factor, ohlcv)
    except factor_service.FactorValidationError:
        return None


def catalog_for_user(
    db: Session,
    owner_id: uuid.UUID,
    *,
    project_id: uuid.UUID | None = None,
    symbol: str | None = None,
    timeframe: str = "1d",
) -> dict:
    """用户因子资产目录 + 同项目冗余对 (正交 R²)。"""
    q = select(Factor).where(Factor.owner_id == owner_id).order_by(Factor.created_at.desc())
    if project_id is not None:
        q = q.where(Factor.project_id == project_id)
    factors = list(db.execute(q.limit(50)).scalars().all())

    ohlcv = None
    sym = (symbol or "").upper()
    if sym:
        user = db.get(User, owner_id)
        if user is not None:
            try:
                ohlcv = mdp.load_for_user(db, user, sym, timeframe)
            except mdp.MarketDataAccessError:
                ohlcv = None

    entries: list[dict] = []
    series_map: dict[uuid.UUID, pd.Series] = {}
    for f in factors:
        bt = _latest_backtest(db, f.id)
        val = _latest_validation(db, f.id)
        oos_sharpe = None
        robustness = None
        if val and val.oos:
            oos_sharpe = (val.oos.get("out_of_sample") or {}).get("sharpe")
        if val and val.robustness:
            robustness = val.robustness.get("score")
        if ohlcv is not None and not ohlcv.empty:
            s = _factor_series(db, owner_id, f, ohlcv)
            if s is not None:
                series_map[f.id] = s
        entries.append(
            {
                "factor_id": str(f.id),
                "name": f.name,
                "kind": f.kind,
                "template_type": f.template_type,
                "project_id": str(f.project_id) if f.project_id else None,
                "version": f.version,
                "sharpe": (bt.metrics or {}).get("sharpe") if bt else None,
                "oos_sharpe": oos_sharpe,
                "robustness_score": robustness,
                "symbol": bt.symbol if bt else sym or None,
                "timeframe": timeframe,
            }
        )

    redundancy: list[dict] = []
    ids = list(series_map.keys())
    for i, a_id in enumerate(ids):
        for b_id in ids[i + 1 :]:
            fa = next(x for x in factors if x.id == a_id)
            fb = next(x for x in factors if x.id == b_id)
            if fa.project_id and fa.project_id != fb.project_id:
                continue
            orth = ar.orthogonalize(series_map[a_id], {fb.name: series_map[b_id]})
            r2 = orth.get("r_squared")
            if r2 is None:
                continue
            redundancy.append(
                {
                    "factor_a": str(a_id),
                    "factor_b": str(b_id),
                    "name_a": fa.name,
                    "name_b": fb.name,
                    "r_squared": r2,
                    "verdict": orth.get("verdict"),
                    "high_overlap": r2 >= 0.35,
                }
            )
    redundancy.sort(key=lambda x: -(x.get("r_squared") or 0))

    return {
        "symbol": sym or None,
        "timeframe": timeframe,
        "factors": entries,
        "redundancy_pairs": redundancy[:20],
        "high_overlap_count": sum(1 for r in redundancy if r.get("high_overlap")),
    }

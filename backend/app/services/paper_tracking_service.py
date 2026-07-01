"""纸面跟踪: 验证后每日 NAV 快照与历史查询。"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.factor import Factor
from backend.app.models.paper import PaperSnapshot
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.services import factor_service, market_data
from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.paper_decay import assess_paper_decay


class PaperTrackingError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _latest_success_validation(db: Session, factor_id: uuid.UUID) -> Validation | None:
    return db.execute(
        select(Validation)
        .where(
            Validation.factor_id == factor_id,
            Validation.status == ValidationStatus.SUCCESS.value,
        )
        .order_by(Validation.created_at.desc())
    ).scalars().first()


def compute_paper_nav(
    db: Session,
    factor_id: uuid.UUID,
    owner_id: uuid.UUID,
    *,
    bars: int = 120,
) -> dict:
    """计算因子在最近 bars 上的纸面净值 (不持久化)。"""
    factor = factor_service.get_factor(db, owner_id, factor_id)
    val = _latest_success_validation(db, factor_id)
    if val is None:
        raise PaperTrackingError("需要先完成科学验证")

    from backend.app.models.market import DataSnapshot

    snap = db.get(DataSnapshot, val.snapshot_id) if val.snapshot_id else None
    timeframe = snap.timeframe if snap else "1d"
    symbol = val.symbol
    ohlcv = market_data.load_ohlcv(symbol, timeframe)
    tail = ohlcv.iloc[-bars:] if ohlcv.shape[0] > bars else ohlcv
    signal = factor_service._compute_series(db, owner_id, factor, tail)
    cfg = CostConfig(**(val.cost_config or {}))
    result = run_backtest(signal, tail, cfg)
    equity = result.get("equity_curve") or []
    nav_end = float(equity[-1]["equity"]) if equity else 1.0
    as_of = _bar_as_of_date(tail)

    return {
        "factor_id": str(factor_id),
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": int(tail.shape[0]),
        "as_of_date": as_of.isoformat(),
        "metrics": result.get("metrics") or {},
        "equity_curve": equity,
        "nav_end": nav_end,
        "validation_grade": (val.robustness or {}).get("grade"),
        "note": "纸面跟踪基于最近行情滚动模拟, 非实盘承诺",
    }


def _bar_as_of_date(ohlcv: pd.DataFrame) -> date:
    ts = ohlcv.index[-1]
    if hasattr(ts, "date"):
        return ts.date()
    return pd.Timestamp(ts).date()


def record_snapshot(
    db: Session,
    factor_id: uuid.UUID,
    owner_id: uuid.UUID,
    *,
    bars: int = 120,
) -> PaperSnapshot | None:
    """计算并 upsert 当日纸面快照; 验证未完成则跳过。"""
    preview = compute_paper_nav(db, factor_id, owner_id, bars=bars)
    as_of = date.fromisoformat(preview["as_of_date"])
    equity = preview.get("equity_curve") or []
    tail_pts = equity[-30:] if len(equity) > 30 else equity

    existing = db.execute(
        select(PaperSnapshot).where(
            PaperSnapshot.factor_id == factor_id,
            PaperSnapshot.as_of_date == as_of,
        )
    ).scalars().first()

    if existing:
        existing.symbol = preview["symbol"]
        existing.timeframe = preview["timeframe"]
        existing.bars = preview["bars"]
        existing.nav_end = preview["nav_end"]
        existing.metrics = preview["metrics"]
        existing.equity_tail = tail_pts
        row = existing
    else:
        row = PaperSnapshot(
            factor_id=factor_id,
            owner_id=owner_id,
            symbol=preview["symbol"],
            timeframe=preview["timeframe"],
            as_of_date=as_of,
            bars=preview["bars"],
            nav_end=preview["nav_end"],
            metrics=preview["metrics"],
            equity_tail=tail_pts,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_snapshots(
    db: Session,
    factor_id: uuid.UUID,
    owner_id: uuid.UUID,
    *,
    limit: int = 90,
) -> list[PaperSnapshot]:
    factor_service.get_factor(db, owner_id, factor_id)
    return list(
        db.execute(
            select(PaperSnapshot)
            .where(
                PaperSnapshot.factor_id == factor_id,
                PaperSnapshot.owner_id == owner_id,
            )
            .order_by(PaperSnapshot.as_of_date.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def assess_factor_decay(db: Session, factor_id: uuid.UUID, owner_id: uuid.UUID) -> dict:
    """纸面衰减评估 (对比验证 OOS 与最新纸面指标)。"""
    val = _latest_success_validation(db, factor_id)
    if val is None:
        return assess_paper_decay(validation_oos=None, paper_metrics=None).to_dict()

    preview = None
    try:
        preview = compute_paper_nav(db, factor_id, owner_id)
    except PaperTrackingError:
        preview = None

    rows = list_snapshots(db, factor_id, owner_id, limit=30)
    nav_series = [r.nav_end for r in reversed(rows)]
    if preview and preview.get("nav_end") is not None:
        if not nav_series or nav_series[-1] != preview["nav_end"]:
            nav_series = nav_series + [preview["nav_end"]]

    verdict = assess_paper_decay(
        validation_oos=val.oos,
        paper_metrics=(preview or {}).get("metrics"),
        nav_series=nav_series or None,
    )
    return verdict.to_dict()


def snapshot_history_payload(db: Session, factor_id: uuid.UUID, owner_id: uuid.UUID) -> dict:
    rows = list_snapshots(db, factor_id, owner_id)
    preview = None
    try:
        preview = compute_paper_nav(db, factor_id, owner_id)
    except PaperTrackingError:
        preview = None
    decay = assess_factor_decay(db, factor_id, owner_id)
    return {
        "factor_id": str(factor_id),
        "snapshots": [
            {
                "as_of_date": r.as_of_date.isoformat(),
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "bars": r.bars,
                "nav_end": r.nav_end,
                "metrics": r.metrics,
                "equity_tail": r.equity_tail,
            }
            for r in reversed(rows)
        ],
        "latest_preview": preview,
        "decay": decay,
    }


def factors_eligible_for_daily_snapshot(db: Session) -> list[tuple[uuid.UUID, uuid.UUID]]:
    """所有有成功验证记录的因子 (factor_id, owner_id)。"""
    stmt = (
        select(Validation.factor_id, Validation.owner_id)
        .where(Validation.status == ValidationStatus.SUCCESS.value)
        .distinct()
    )
    return list(db.execute(stmt).all())


def run_daily_paper_batch(db: Session, *, bars: int = 120) -> dict:
    """批量记录纸面快照 (cron / Celery 调用)。"""
    started = datetime.now(timezone.utc)
    ok, skipped, failed = 0, 0, 0
    errors: list[str] = []
    for factor_id, owner_id in factors_eligible_for_daily_snapshot(db):
        try:
            val = _latest_success_validation(db, factor_id)
            if val is None:
                skipped += 1
                continue
            record_snapshot(db, factor_id, owner_id, bars=bars)
            ok += 1
        except PaperTrackingError:
            skipped += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            errors.append(f"{factor_id}: {exc}")
    return {
        "started_at": started.isoformat(),
        "recorded": ok,
        "skipped": skipped,
        "failed": failed,
        "errors": errors[:20],
    }

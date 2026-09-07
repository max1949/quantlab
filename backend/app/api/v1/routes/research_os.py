"""Research / Evidence OS HTTP surface — thin wrap of engine (QLN UI closure)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services import research_os_service as ros

router = APIRouter()


@router.get("/doctrine", summary="产品教义：先证明再下注")
def doctrine(_user: Annotated[User, Depends(get_current_user)]) -> dict[str, Any]:
    return ros.doctrine_nav()


@router.get("/strategies", summary="策略包列表（Spec v2）")
def strategies(_user: Annotated[User, Depends(get_current_user)]) -> dict[str, Any]:
    items = ros.list_strategy_packages()
    return {"items": items, "n": len(items), "title_zh": "策略规格包"}


@router.get("/strategies/{strategy_id}", summary="策略包详情 / Contract / lineage")
def strategy_detail(
    strategy_id: str,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        return ros.get_strategy_package(strategy_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/strategies/diff/{a_id}/{b_id}", summary="Spec 语义差异")
def strategy_diff(
    a_id: str,
    b_id: str,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        return ros.semantic_diff_packages(a_id, b_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/evidence/run", summary="跑证据流水线 → 建议晋级/暂缓/淘汰")
def evidence_run(
    _user: Annotated[User, Depends(get_current_user)],
    strategy_id: str = Query("hist_fl_momentum_w20"),
    instrument: str = Query("RB"),
    bars: int = Query(504, ge=120, le=2000),
) -> dict[str, Any]:
    try:
        return ros.run_evidence_for_strategy(strategy_id, instrument=instrument, bars=bars)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/experiments", summary="实验账本（非参数扫描）")
def experiments(
    _user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    return ros.list_experiments(limit=limit)


@router.get("/experiments/{experiment_id}", summary="实验详情 / 数据信任 / 假设")
def experiment_detail(
    experiment_id: str,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        return ros.get_experiment(experiment_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/experiments/{experiment_id}/reproduce", summary="复现实验")
def experiment_reproduce(
    experiment_id: str,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        return ros.reproduce_by_id(experiment_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/paper/factor-sign", summary="canonical factor_sign PaperRun")
def paper_factor_sign(
    _user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    strategy_id: str = Query("hist_fl_momentum_w20"),
    instrument: str = Query("RB"),
    bars: int = Query(400, ge=80, le=2000),
) -> dict[str, Any]:
    try:
        out = ros.run_factor_sign_paper_api(strategy_id, instrument=instrument, bars=bars)
        sealed = ros.seal_factor_sign_paper_run(db, _user, out)
        out["paper_run_id"] = sealed.get("paper_run_id")
        out["challenge_credit_zh"] = sealed.get("challenge_credit_zh")
        return out
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/shadow", summary="影子对照 / 飞行记录")
def shadow(
    _user: Annotated[User, Depends(get_current_user)],
    strategy_id: str = Query("hist_fl_momentum_w20"),
    instrument: str = Query("RB"),
    bars: int = Query(120, ge=60, le=504),
) -> dict[str, Any]:
    try:
        return ros.shadow_desk(strategy_id, instrument=instrument, bars=bars)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/portfolio/governor", summary="组合治理")
def governor(_user: Annotated[User, Depends(get_current_user)]) -> dict[str, Any]:
    return ros.portfolio_governor_view()


@router.get("/dna/{strategy_id}", summary="策略 DNA / 谱系 / 坟场")
def dna(
    strategy_id: str,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        return ros.dna_desk(strategy_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/live-readiness", summary="实盘资格卡（申请≠已允许）")
def live_readiness(_user: Annotated[User, Depends(get_current_user)]) -> dict[str, Any]:
    return ros.live_readiness_card()

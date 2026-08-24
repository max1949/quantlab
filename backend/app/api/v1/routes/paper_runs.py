"""Phase 6 PaperRun API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import require_feature
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.paper_run import (
    BacktestPaperCompareOut,
    PaperAnalystIn,
    PaperAnalystOut,
    PaperDashboardOut,
    PaperReadyIn,
    PaperRunCreateIn,
    PaperRunOut,
)
from backend.app.services import audit_service, paper_run_service as prs
from engine.trading.execution_environment import EnvironmentGateError

router = APIRouter()


@router.post("/paper-ready", summary="登记 PAPER_READY（绑定 spec 版本）")
def register_paper_ready(
    payload: PaperReadyIn,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        row = prs.register_paper_ready(
            db,
            current_user,
            spec_payload=payload.spec,
            compiled_hash=payload.compiled_hash,
            data_gate_status=payload.data_gate_status,
            backtest_pass=payload.backtest_pass,
            validation_pass=payload.validation_pass,
            robustness_pass=payload.robustness_pass,
        )
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {
        "strategy_spec_id": row.strategy_spec_id,
        "strategy_spec_version": row.strategy_spec_version,
        "strategy_spec_hash": row.strategy_spec_hash,
        "paper_ready": True,
    }


@router.post("/runs", response_model=PaperRunOut, status_code=status.HTTP_201_CREATED, summary="创建 PaperRun")
def create_paper_run(
    payload: PaperRunCreateIn,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperRunOut:
    try:
        run = prs.create_paper_run(
            db,
            current_user,
            spec_payload=payload.spec,
            compiled_hash=payload.compiled_hash,
            environment=payload.environment,
            instrument=payload.instrument,
            data_provider=payload.data_provider,
            starting_balance=payload.starting_balance,
        )
    except EnvironmentGateError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="paper_run.create",
        resource_type="paper_run",
        resource_id=str(run.id),
        detail={"environment": run.environment, "instrument": run.instrument},
    )
    return PaperRunOut(**prs.paper_run_to_dict(run))


@router.post("/runs/{run_id}/start", response_model=PaperRunOut, summary="启动 paper-runner")
def start_paper_run(
    run_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperRunOut:
    try:
        run = prs.start_paper_run(db, current_user.id, uuid.UUID(run_id))
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return PaperRunOut(**prs.paper_run_to_dict(run))


@router.post("/runs/{run_id}/stop", response_model=PaperRunOut, summary="优雅停止 PaperRun")
def stop_paper_run(
    run_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperRunOut:
    try:
        run = prs.stop_paper_run(db, current_user.id, uuid.UUID(run_id))
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return PaperRunOut(**prs.paper_run_to_dict(run))


@router.post("/runs/{run_id}/kill", response_model=PaperRunOut, summary="Kill Switch — 终止 PaperRun")
def kill_paper_run(
    run_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperRunOut:
    try:
        run = prs.kill_paper_run(db, current_user.id, uuid.UUID(run_id))
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return PaperRunOut(**prs.paper_run_to_dict(run))


@router.get("/runs/{run_id}/dashboard", response_model=PaperDashboardOut, summary="模拟交易仪表盘")
def paper_dashboard(
    run_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperDashboardOut:
    try:
        data = prs.paper_run_dashboard(db, current_user.id, uuid.UUID(run_id))
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PaperDashboardOut(**data)


@router.post("/runs/{run_id}/analyst", response_model=PaperAnalystOut, summary="AI Paper Analyst（只解释）")
def paper_analyst(
    run_id: str,
    payload: PaperAnalystIn,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperAnalystOut:
    try:
        dash = prs.paper_run_dashboard(db, current_user.id, uuid.UUID(run_id))
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    q = payload.question.strip()
    evidence = [
        f"状态：{dash['status_zh']}",
        f"持仓：{dash['position_zh']}",
        f"累计盈亏：{dash['total_pnl_zh']}",
        f"数据：{dash['data_connection_zh']}",
    ]
    if dash["recent_signals"]:
        s0 = dash["recent_signals"][0]
        evidence.append(f"最近信号：{s0['decision']} — {s0['reason']}")

    if "亏损" in q or "为什么" in q:
        answer = (
            "根据当前模拟运行记录："
            f"累计 {dash['total_pnl_zh']}，持仓 {dash['position_zh']}。"
            "可能原因包括：趋势信号与实时行情节奏差异、模拟成交滑点、或风控暂停后未开新仓。"
            "（AI 仅解释，不会修改策略或解除 Kill Switch。）"
        )
    else:
        answer = (
            f"模拟运行 {dash['strategy_name']}@{dash['strategy_version']} "
            f"当前{dash['status_zh']}；{dash['disclaimer_zh']}。"
        )
    return PaperAnalystOut(answer_zh=answer, evidence=evidence)


@router.get(
    "/runs/{run_id}/backtest-vs-paper",
    response_model=BacktestPaperCompareOut,
    summary="回测 vs 模拟差异报告",
)
def backtest_vs_paper(
    run_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> BacktestPaperCompareOut:
    try:
        data = prs.backtest_vs_paper_report(db, current_user.id, uuid.UUID(run_id))
    except prs.PaperRunError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BacktestPaperCompareOut(**data)

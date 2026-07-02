"""因子参数扫描服务 — 网格回测 + 实验存档 + 教练解读。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.factor_scan import FactorScan
from backend.app.models.user import User
from backend.app.services import factor_service, market_data_policy as mdp
from engine import factor_engine as fe
from engine.param_scan import scan_template_grid
from engine.factor_metrics import IC_HORIZON_BY_TF
from engine.research_quality import assess_scan_preview


class ScanError(Exception):
    pass


def _ic_horizon(timeframe: str) -> int:
    return IC_HORIZON_BY_TF.get(timeframe, 1)


def _coach_summary(template_type: str, results: list[dict], symbol: str, timeframe: str) -> str:
    if not results:
        return "扫描未产生有效结果，请换标的或模板重试。"
    top = results[0]
    params = top.get("params") or {}
    score = top.get("score")
    oos = top.get("oos_sharpe")
    ic = (top.get("ic") or {}).get("ic_mean")
    turnover = (top.get("metrics") or {}).get("turnover")
    lines = [
        f"在 {symbol} · {timeframe} 上对「{template_type}」完成了 {len(results)} 组参数扫描。",
        f"当前最优: {top.get('label')}，综合分 {score}。",
    ]
    if oos is not None and oos < 0.3:
        lines.append("样本外夏普偏弱，建议缩小参数搜索范围或换周期后再验证。")
    elif oos is not None and oos >= 0.5:
        lines.append("样本外表现尚可，可一键载入该参数并跑完整科学验证。")
    if ic is not None and abs(ic) < 0.02:
        lines.append("IC 偏低，因子预测力有限，可尝试组合因子或换模板。")
    if turnover is not None and turnover > 40:
        lines.append("换手率偏高，中频实盘成本可能侵蚀收益，注意成本敏感性分析。")
    return " ".join(lines)


def _serialize_row(row: dict) -> dict:
    m = row.get("metrics") or {}
    ic = row.get("ic") or {}
    preview = assess_scan_preview(
        sharpe=m.get("sharpe"),
        oos_sharpe=row.get("oos_sharpe"),
        ic_mean=ic.get("ic_mean"),
        turnover=m.get("turnover"),
    )
    return {
        "rank": row.get("rank", 0),
        "params": row.get("params") or {},
        "label": row.get("label") or "",
        "score": row.get("score"),
        "sharpe": m.get("sharpe"),
        "oos_sharpe": row.get("oos_sharpe"),
        "ic_mean": ic.get("ic_mean"),
        "turnover": m.get("turnover"),
        "max_drawdown": m.get("max_drawdown"),
        "publish_promising": preview.promising,
        "publish_hints": preview.hints,
    }


def run_scan(
    db: Session,
    user: User,
    *,
    symbol: str,
    template_type: str,
    timeframe: str = "1d",
    project_id: uuid.UUID | None = None,
    steps: int = 8,
) -> FactorScan:
    if template_type not in fe.TEMPLATES:
        raise ScanError(f"不支持的模板: {template_type}")
    ohlcv = mdp.load_for_user(db, user, symbol, timeframe)
    if ohlcv is None or ohlcv.empty:
        raise ScanError("行情数据为空")
    results = scan_template_grid(
        ohlcv,
        template_type,
        steps=steps,
        ic_horizon=_ic_horizon(timeframe),
    )
    best = results[0] if results else None
    coach = _coach_summary(template_type, results, symbol, timeframe)
    scan = FactorScan(
        owner_id=user.id,
        project_id=project_id,
        symbol=symbol.upper(),
        timeframe=timeframe,
        template_type=template_type,
        results=results,
        best_params=best.get("params") if best else None,
        best_score=best.get("score") if best else None,
        coach_summary=coach,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    from backend.app.services import academy_hooks

    scan.academy_rewards = academy_hooks.on_factor_scan(db, user)
    return scan


def list_scans(
    db: Session,
    owner_id: uuid.UUID,
    *,
    project_id: uuid.UUID | None = None,
    limit: int = 20,
) -> list[FactorScan]:
    q = select(FactorScan).where(FactorScan.owner_id == owner_id)
    if project_id is not None:
        q = q.where(FactorScan.project_id == project_id)
    return list(
        db.execute(q.order_by(FactorScan.created_at.desc()).limit(limit)).scalars().all()
    )


def get_scan(db: Session, owner_id: uuid.UUID, scan_id: uuid.UUID) -> FactorScan | None:
    row = db.get(FactorScan, scan_id)
    if row is None or row.owner_id != owner_id:
        return None
    return row


def apply_scan(
    db: Session,
    user: User,
    scan_id: uuid.UUID,
    *,
    rank: int = 1,
    name: str | None = None,
) -> tuple[FactorScan, object]:
    scan = get_scan(db, user.id, scan_id)
    if scan is None:
        raise ScanError("扫描记录不存在")
    rows = scan.results or []
    picked = next((r for r in rows if r.get("rank") == rank), None)
    if picked is None and rows:
        picked = rows[min(rank - 1, len(rows) - 1)]
    if picked is None:
        raise ScanError("无可用扫描结果")
    params = picked.get("params") or scan.best_params
    if not params:
        raise ScanError("参数为空")
    factor_name = name or f"{scan.template_type}-{scan.symbol}-scan{rank}"
    factor = factor_service.create_template_factor(
        db,
        user,
        factor_name,
        scan.template_type,
        params,
        project_id=scan.project_id,
    )
    scan.applied_factor_id = factor.id
    db.commit()
    db.refresh(scan)
    return scan, factor


def _top_row(scan: FactorScan) -> dict | None:
    rows = scan.results or []
    return rows[0] if rows else None


def compare_scans(
    db: Session,
    owner_id: uuid.UUID,
    scan_id_a: uuid.UUID,
    scan_id_b: uuid.UUID,
) -> dict:
    a = get_scan(db, owner_id, scan_id_a)
    b = get_scan(db, owner_id, scan_id_b)
    if a is None or b is None:
        raise ScanError("扫描记录不存在")
    top_a = _top_row(a)
    top_b = _top_row(b)
    if top_a is None or top_b is None:
        raise ScanError("扫描结果为空，无法对比")

    def _metric(row: dict, key: str) -> float | None:
        if key in ("sharpe", "turnover", "max_drawdown"):
            return (row.get("metrics") or {}).get(key)
        if key == "oos_sharpe":
            return row.get("oos_sharpe")
        if key == "score":
            return row.get("score")
        if key == "ic_mean":
            return (row.get("ic") or {}).get("ic_mean")
        return None

    metrics = ("score", "sharpe", "oos_sharpe", "ic_mean", "turnover")
    delta: dict[str, float | None] = {}
    for m in metrics:
        va, vb = _metric(top_a, m), _metric(top_b, m)
        delta[m] = (va - vb) if va is not None and vb is not None else None

    score_a = top_a.get("score") or 0
    score_b = top_b.get("score") or 0
    if score_a > score_b:
        winner = "a"
    elif score_b > score_a:
        winner = "b"
    else:
        winner = "tie"

    summary = (
        f"A ({a.template_type}·{a.timeframe}) 最优 {top_a.get('label')} "
        f"综合分 {top_a.get('score')}；"
        f"B ({b.template_type}·{b.timeframe}) 最优 {top_b.get('label')} "
        f"综合分 {top_b.get('score')}。"
    )
    if winner == "a":
        summary += " 当前 A 更优，可优先载入 A 的参数。"
    elif winner == "b":
        summary += " 当前 B 更优，可优先载入 B 的参数。"
    else:
        summary += " 两者接近，建议结合 IC 与换手再做取舍。"

    return {
        "scan_a": scan_to_out(a),
        "scan_b": scan_to_out(b),
        "delta": delta,
        "winner": winner,
        "summary": summary,
    }


def scan_to_out(scan: FactorScan) -> dict:
    rows = [_serialize_row(r) for r in (scan.results or [])]
    return {
        "id": scan.id,
        "symbol": scan.symbol,
        "timeframe": scan.timeframe,
        "template_type": scan.template_type,
        "project_id": scan.project_id,
        "results": rows,
        "best_params": scan.best_params,
        "best_score": scan.best_score,
        "coach_summary": scan.coach_summary,
        "applied_factor_id": scan.applied_factor_id,
        "created_at": scan.created_at,
    }

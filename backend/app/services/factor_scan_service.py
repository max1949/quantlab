"""因子参数扫描服务 — 网格回测 + 实验存档 + 教练解读。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.factor import Factor, FactorKind
from backend.app.models.factor_scan import FactorScan
from backend.app.models.user import User
from backend.app.services import factor_service, market_data_policy as mdp
from engine import factor_engine as fe
from engine.param_scan import (
    build_param_grid,
    build_random_param_grid,
    scan_stack_weights,
    scan_template_grid,
    scan_template_multi_symbol,
    scan_template_multi_refine,
    scan_template_refine,
)
from engine.factor_metrics import IC_HORIZON_BY_TF
from engine.research_quality import assess_scan_preview
from engine.data_quality import assess_ohlcv_quality


class ScanError(Exception):
    pass


def _ic_horizon(timeframe: str) -> int:
    return IC_HORIZON_BY_TF.get(timeframe, 1)


def _coach_summary(
    template_type: str,
    results: list[dict],
    symbol: str,
    timeframe: str,
    *,
    multi_symbol: bool = False,
) -> str:
    if not results:
        return "扫描未产生有效结果，请换标的或模板重试。"
    top = results[0]
    params = top.get("params") or {}
    score = top.get("score")
    oos = top.get("oos_sharpe")
    ic = (top.get("ic") or {}).get("ic_mean")
    turnover = (top.get("metrics") or {}).get("turnover")
    scope = f"{symbol}（跨标的平均）" if multi_symbol else symbol
    lines = [
        f"在 {scope} · {timeframe} 上对「{template_type}」完成了 {len(results)} 组参数扫描。",
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
        "symbol_breakdown": row.get("symbol_breakdown"),
    }


def _stack_coach_summary(
    factor_names: list[str],
    results: list[dict],
    symbol: str,
    timeframe: str,
) -> str:
    if not results:
        return "组合权重扫描未产生有效结果，请换因子或标的重试。"
    top = results[0]
    lines = [
        f"在 {symbol} · {timeframe} 上对「{' + '.join(factor_names)}」完成了 {len(results)} 组权重扫描。",
        f"当前最优: {top.get('label')}，综合分 {top.get('score')}。",
    ]
    oos = top.get("oos_sharpe")
    if oos is not None and oos < 0.3:
        lines.append("样本外偏弱，可尝试换一组基础因子或调整权重范围。")
    elif oos is not None and oos >= 0.5:
        lines.append("组合表现尚可，可一键载入该权重并跑完整科学验证。")
    return " ".join(lines)


def _load_stack_factors(
    db: Session,
    user: User,
    factor_ids: list[uuid.UUID],
    *,
    project_id: uuid.UUID | None = None,
) -> list[Factor]:
    if len(factor_ids) != 2:
        raise ScanError("组合权重扫描需要恰好 2 个因子")
    factors: list[Factor] = []
    for fid in factor_ids:
        factor = db.get(Factor, fid)
        if factor is None or factor.owner_id != user.id:
            raise ScanError("因子不存在或无权使用")
        if factor.kind not in (
            FactorKind.TEMPLATE.value,
            FactorKind.FORMULA.value,
        ):
            raise ScanError("组合扫描仅支持模板或公式因子")
        if project_id is not None and factor.project_id != project_id:
            raise ScanError("所选因子须属于当前项目")
        factors.append(factor)
    if user.level < 1:
        raise ScanError("组合权重扫描需要 L1")
    return factors


def _run_stack_scan(
    db: Session,
    user: User,
    *,
    symbol: str,
    factor_ids: list[uuid.UUID],
    timeframe: str = "1d",
    project_id: uuid.UUID | None = None,
    steps: int = 8,
) -> FactorScan:
    factors = _load_stack_factors(db, user, factor_ids, project_id=project_id)
    ohlcv = mdp.load_for_user(db, user, symbol.upper(), timeframe)
    if ohlcv is None or ohlcv.empty:
        raise ScanError("行情数据为空")

    components: list[tuple[str, object]] = []
    for factor in factors:
        def make_fn(f: Factor):
            def fn(df):
                return factor_service.compute_factor_series(db, user.id, f, df)

            return fn

        components.append((factor.name, make_fn(factor)))

    results = scan_stack_weights(
        ohlcv,
        components,
        ic_horizon=_ic_horizon(timeframe),
        steps=steps,
        factor_ids=[str(f.id) for f in factors],
    )
    best = results[0] if results else None
    names = [f.name for f in factors]
    coach = _stack_coach_summary(names, results, symbol.upper(), timeframe)
    dq = assess_ohlcv_quality(ohlcv, timeframe)
    if dq.get("warnings"):
        coach = f"【数据质量】{'；'.join(dq['warnings'][:2])} {coach}"
    template_key = f"stack:{factors[0].id},{factors[1].id}"
    scan = FactorScan(
        owner_id=user.id,
        project_id=project_id,
        symbol=symbol.upper(),
        timeframe=timeframe,
        template_type=template_key,
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


def run_scan(
    db: Session,
    user: User,
    *,
    symbol: str,
    template_type: str,
    timeframe: str = "1d",
    project_id: uuid.UUID | None = None,
    steps: int = 8,
    symbols: list[str] | None = None,
    search_mode: str = "grid",
    factor_ids: list[uuid.UUID] | None = None,
) -> FactorScan:
    if factor_ids:
        return _run_stack_scan(
            db,
            user,
            symbol=symbol,
            factor_ids=factor_ids,
            timeframe=timeframe,
            project_id=project_id,
            steps=steps,
        )
    if template_type not in fe.TEMPLATES:
        raise ScanError(f"不支持的模板: {template_type}")
    sym_list = [s.strip().upper() for s in (symbols or [symbol]) if s and s.strip()]
    if not sym_list:
        sym_list = [symbol.upper()]
    sym_list = list(dict.fromkeys(sym_list))[:3]
    multi = len(sym_list) > 1
    mode = (search_mode or "grid").lower()
    refine_meta = ""
    if mode == "refine":
        if multi:
            ohlcv_map: dict = {}
            for s in sym_list:
                df = mdp.load_for_user(db, user, s, timeframe)
                if df is None or df.empty:
                    raise ScanError(f"{s} 行情数据为空")
                ohlcv_map[s] = df
            results, refine_meta = scan_template_multi_refine(
                ohlcv_map,
                template_type,
                ic_horizon=_ic_horizon(timeframe),
                steps=steps,
            )
            symbol_label = ",".join(sym_list)
            dq_notes: list[str] = []
            for s, df in ohlcv_map.items():
                dq = assess_ohlcv_quality(df, timeframe)
                dq_notes.extend([f"{s}:{w}" for w in dq.get("warnings", [])[:1]])
        else:
            s = sym_list[0]
            ohlcv = mdp.load_for_user(db, user, s, timeframe)
            if ohlcv is None or ohlcv.empty:
                raise ScanError("行情数据为空")
            results, refine_meta = scan_template_refine(
                ohlcv,
                template_type,
                ic_horizon=_ic_horizon(timeframe),
                steps=steps,
            )
            symbol_label = s
            dq = assess_ohlcv_quality(ohlcv, timeframe)
            dq_notes = dq.get("warnings") or []
    elif mode == "random":
        param_grid = build_random_param_grid(template_type, n_trials=steps)
        scan_kwargs = {"param_grid": param_grid, "steps": steps}
    else:
        scan_kwargs = {"steps": steps}

    if mode != "refine":
        if multi:
            ohlcv_map = {}
            for s in sym_list:
                df = mdp.load_for_user(db, user, s, timeframe)
                if df is None or df.empty:
                    raise ScanError(f"{s} 行情数据为空")
                ohlcv_map[s] = df
            results = scan_template_multi_symbol(
                ohlcv_map,
                template_type,
                ic_horizon=_ic_horizon(timeframe),
                **scan_kwargs,
            )
            symbol_label = ",".join(sym_list)
            dq_notes = []
            for s, df in ohlcv_map.items():
                dq = assess_ohlcv_quality(df, timeframe)
                dq_notes.extend([f"{s}:{w}" for w in dq.get("warnings", [])[:1]])
        else:
            s = sym_list[0]
            ohlcv = mdp.load_for_user(db, user, s, timeframe)
            if ohlcv is None or ohlcv.empty:
                raise ScanError("行情数据为空")
            results = scan_template_grid(
                ohlcv,
                template_type,
                ic_horizon=_ic_horizon(timeframe),
                **scan_kwargs,
            )
            symbol_label = s
            dq = assess_ohlcv_quality(ohlcv, timeframe)
            dq_notes = dq.get("warnings") or []

    best = results[0] if results else None
    coach = _coach_summary(
        template_type, results, symbol_label, timeframe, multi_symbol=multi
    )
    if dq_notes:
        coach = f"【数据质量】{'；'.join(dq_notes[:2])} {coach}"
    if mode == "random":
        coach = f"【随机搜索 {steps} 组】{coach}"
    elif mode == "refine" and refine_meta:
        coach = f"{refine_meta}{coach}"
    scan = FactorScan(
        owner_id=user.id,
        project_id=project_id,
        symbol=symbol_label,
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
    symbol: str | None = None,
    template_type: str | None = None,
    limit: int = 50,
) -> list[FactorScan]:
    q = select(FactorScan).where(FactorScan.owner_id == owner_id)
    if project_id is not None:
        q = q.where(FactorScan.project_id == project_id)
    if symbol:
        q = q.where(FactorScan.symbol == symbol.upper())
    if template_type:
        q = q.where(FactorScan.template_type == template_type)
    cap = max(1, min(int(limit), 100))
    return list(
        db.execute(q.order_by(FactorScan.created_at.desc()).limit(cap)).scalars().all()
    )


def project_titles_for(db: Session, scans: list[FactorScan]) -> dict[uuid.UUID, str]:
    pids = {s.project_id for s in scans if s.project_id}
    if not pids:
        return {}
    from backend.app.models.project import ResearchProject

    rows = db.execute(
        select(ResearchProject.id, ResearchProject.title).where(ResearchProject.id.in_(pids))
    ).all()
    return {row[0]: row[1] for row in rows}


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
    if scan.template_type.startswith("stack:"):
        weights = params.get("weights")
        if not weights:
            raise ScanError("组合权重为空")
        components = [
            {"factor_id": str(w["factor_id"]), "weight": float(w["weight"])}
            for w in weights
        ]
        factor = factor_service.create_stack_factor(
            db,
            user,
            factor_name,
            components,
            project_id=scan.project_id,
        )
    else:
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


def scan_to_out(scan: FactorScan, *, project_title: str | None = None) -> dict:
    rows = [_serialize_row(r) for r in (scan.results or [])]
    return {
        "id": scan.id,
        "symbol": scan.symbol,
        "timeframe": scan.timeframe,
        "template_type": scan.template_type,
        "project_id": scan.project_id,
        "project_title": project_title,
        "results": rows,
        "best_params": scan.best_params,
        "best_score": scan.best_score,
        "coach_summary": scan.coach_summary,
        "applied_factor_id": scan.applied_factor_id,
        "created_at": scan.created_at,
    }

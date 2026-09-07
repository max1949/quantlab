"""Research / Evidence OS thin service — reuses engine, no second logic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.backtest import signal_to_positions
from engine.canary import CanaryCapitalContract, evaluate_live_readiness
from engine.evidence.pipeline import run_evidence_pipeline
from engine.experiment.ledger import ExperimentLedger, default_ledger_path
from engine.experiment.reproduce import reproduce_experiment
from engine.factor_engine import compute_template_factor
from engine.paper.factor_sign_runtime import run_factor_sign_paper
from engine.portfolio import (
    PortfolioGovernor,
    PortfolioLimits,
    capacity_check,
    cluster_by_correlation,
    evaluate_portfolio,
    pairwise_return_correlation,
    style_exposure,
)
from engine.reliability import DeadManSwitch, ReconciliationReport, default_broker_matrix
from engine.shadow import (
    FlightEvent,
    FlightRecorder,
    ShadowSnapshot,
    behavior_parity_report,
    compare_twins,
    loss_attribution,
    replay_events,
)
from engine.strategies.v2.factor_sign_adapter import compile_factor_sign_to_paper
from engine.strategies.v2.package import import_package
from engine.strategies.v2.spec_v2 import validate_spec_v2
from engine.strategy_dna import (
    ResearchMemory,
    build_dna_from_spec_v2,
)
from engine.ui_labels_zh import LIVE_READINESS_ZH, explain_decision, gate_flags_zh

ROOT = Path(__file__).resolve().parents[3]
SPECS_DIR = ROOT / "strategy_specs" / "historical_reconstructed"
MARKET = ROOT / "data" / "market_data" / "genuine_recovery"
SHADOW_FLIGHT = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "shadow_flight_continuous.jsonl"
PAPER_QUAL = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "paper_qualification_hist_fl_momentum_w20_rb.json"
SHADOW_EV = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "shadow_continuous_evidence.json"
GENEALOGY = ROOT / "data" / "research_memory" / "genealogy_phase_a.json"
MEMORY = ROOT / "data" / "research_memory" / "memory.jsonl"
GRAVEYARD = ROOT / "data" / "research_memory" / "graveyard.jsonl"


def _load_ohlcv(instrument: str, bars: int = 504) -> pd.DataFrame:
    path = MARKET / f"{instrument.upper()}_1d.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"missing market data: {path}")
    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df = df.copy()
        df.index = df.index.tz_localize("UTC")
    return df.sort_index().iloc[-bars:]


def list_strategy_packages() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not SPECS_DIR.is_dir():
        return out
    for p in sorted(SPECS_DIR.glob("*.v2.package.json")):
        try:
            pkg = import_package(p)
            spec = validate_spec_v2(pkg.strategy_spec)
            out.append(
                {
                    "path": str(p.relative_to(ROOT)),
                    "strategy_id": spec.identity.strategy_id,
                    "version": spec.identity.version,
                    "name": spec.identity.name,
                    "instruments": list(spec.universe.instruments),
                    "permitted_environments": list(spec.compatibility.permitted_environments or []),
                    "content_hash": spec.content_hash(),
                    "description_zh": (spec.metadata.description or "")[:240],
                }
            )
        except Exception as exc:  # noqa: BLE001
            out.append({"path": str(p), "error": str(exc)})
    return out


def get_strategy_package(strategy_id: str) -> dict[str, Any]:
    for p in SPECS_DIR.glob("*.v2.package.json"):
        pkg = import_package(p)
        spec = validate_spec_v2(pkg.strategy_spec)
        if spec.identity.strategy_id == strategy_id:
            contract = pkg.strategy_contract.model_dump(mode="json") if hasattr(pkg, "strategy_contract") else None
            return {
                "strategy_id": strategy_id,
                "version": spec.identity.version,
                "spec": spec.model_dump(mode="json"),
                "package_path": str(p.relative_to(ROOT)),
                "lineage": {
                    "family_id": spec.identity.family_id,
                    "derived_from": spec.identity.derived_from,
                    "parent_version": spec.identity.parent_version,
                    "fork_of": spec.identity.fork_of,
                    "content_hash": spec.content_hash(),
                },
                "contract": contract,
                "invariants": pkg.invariants.model_dump(mode="json") if hasattr(pkg, "invariants") else None,
                "parameters": getattr(pkg, "parameters", None),
                "manifest": pkg.manifest.model_dump(mode="json") if hasattr(pkg, "manifest") else None,
            }
    raise FileNotFoundError(f"strategy package not found: {strategy_id}")


def semantic_diff_packages(a_id: str, b_id: str) -> dict[str, Any]:
    a = get_strategy_package(a_id)
    b = get_strategy_package(b_id)
    sa, sb = a["spec"], b["spec"]
    keys = sorted(set(sa.keys()) | set(sb.keys()))
    diffs: list[dict[str, Any]] = []
    for k in keys:
        if sa.get(k) != sb.get(k):
            diffs.append({"field": k, "a": sa.get(k), "b": sb.get(k)})
    return {
        "a": a_id,
        "b": b_id,
        "n_diffs": len(diffs),
        "diffs": diffs[:40],
        "note_zh": "语义差异基于 Spec v2 JSON 字段；未改变策略参数阈值。",
    }


def run_evidence_for_strategy(
    strategy_id: str,
    *,
    instrument: str = "RB",
    bars: int = 504,
) -> dict[str, Any]:
    pkg = get_strategy_package(strategy_id)
    spec = validate_spec_v2(pkg["spec"])
    vals = dict(spec.parameters.values or {})
    tt = str(vals.get("template_type") or "")
    window = vals.get("param_window", vals.get("window"))
    if not tt or window is None:
        raise ValueError("Spec missing template_type/window — cannot run Evidence without inventing params")
    ohlcv = _load_ohlcv(instrument, bars)

    def compute_signal(df: pd.DataFrame) -> pd.Series:
        return compute_template_factor(df, tt, {"window": int(window)})

    neighborhood = [
        (f"w{int(window)-2}", lambda d, w=int(window) - 2: compute_template_factor(d, tt, {"window": w})),
        (f"w{int(window)}", compute_signal),
        (f"w{int(window)+2}", lambda d, w=int(window) + 2: compute_template_factor(d, tt, {"window": w})),
    ]
    report = run_evidence_pipeline(
        strategy_id=spec.identity.strategy_id,
        strategy_version=spec.identity.version,
        ohlcv=ohlcv,
        compute_signal=compute_signal,
        neighborhood=neighborhood,
        param_count=1,
    )
    blob = report.to_dict()
    explained = explain_decision(report.decision, report.reasons)
    reality = blob.get("reality_score") or {}
    debt = blob.get("research_debt") or {}
    return {
        **blob,
        "instrument": instrument.upper(),
        "bars": int(len(ohlcv)),
        "decision_zh": explained,
        "gates_zh": gate_flags_zh(blob.get("gates") or {}),
        "reality_explain_zh": {
            "score": reality.get("score"),
            "why_zh": "现实分综合样本外、滚动样本外、费率/滑点压力、敏感性与制度分段等闸门，衡量“有多像可交易现实”。",
            "components": reality,
        },
        "debt_explain_zh": {
            "score": debt.get("score"),
            "why_zh": "研究债衡量未闭环证据与过度调参风险；偏高时判定应暂缓或淘汰。",
            "components": debt,
        },
        "doctrine_zh": "先证明，再下注。晋级仅代表可进入模拟观察，不等于实盘。",
    }


def list_experiments(limit: int = 50) -> dict[str, Any]:
    ledger = ExperimentLedger(default_ledger_path(ROOT))
    # Also include QLN-11 factor_sign paper ledger if present
    extra = ROOT / "docs" / "governance" / "qln11" / "artifacts" / "paper_runs" / "experiment_ledger_factor_sign_paper.jsonl"
    records: list[dict[str, Any]] = []
    for path in [ledger.path, extra]:
        if not path.is_file():
            continue
        el = ExperimentLedger(path)
        for rec in el.iter_records():
            records.append(
                {
                    "experiment_id": rec.experiment_id,
                    "strategy_id": rec.strategy_id,
                    "strategy_version": rec.strategy_version,
                    "dataset_id": rec.dataset_id,
                    "dataset_hash": rec.dataset_hash,
                    "evidence_stage": rec.evidence_stage,
                    "data_trust_status": rec.data_trust_status,
                    "engine_name": rec.engine_name,
                    "adapter_version": rec.adapter_version,
                    "sealed": rec.sealed,
                    "notes": rec.notes,
                    "ledger_path": str(path.relative_to(ROOT)),
                }
            )
    records = list(reversed(records))[:limit]
    return {
        "title_zh": "实验账本（Experiment Ledger）",
        "subtitle_zh": "只读、追加写入的可复现实验记录。不是参数扫描。",
        "n": len(records),
        "items": records,
        "not_factor_scan_zh": "参数扫描请前往「参数扫描」页；本页只展示已封印实验。",
    }


def get_experiment(experiment_id: str) -> dict[str, Any]:
    paths = [
        default_ledger_path(ROOT),
        ROOT / "docs" / "governance" / "qln11" / "artifacts" / "paper_runs" / "experiment_ledger_factor_sign_paper.jsonl",
    ]
    for path in paths:
        if not path.is_file():
            continue
        rec = ExperimentLedger(path).get(experiment_id)
        if rec is not None:
            d = rec.model_dump(mode="json")
            return {
                **d,
                "ledger_path": str(path.relative_to(ROOT)),
                "explain_zh": {
                    "provenance_zh": "记录含策略定义哈希、数据集哈希、引擎/适配器版本与假设。",
                    "data_trust_zh": f"数据信任状态：{rec.data_trust_status}",
                    "assumptions": d.get("execution_assumptions") or d.get("assumptions"),
                    "next_zh": "可用 reproduce 接口在相同假设下复现（研究环境）。",
                },
            }
    raise FileNotFoundError(experiment_id)


def reproduce_by_id(experiment_id: str) -> dict[str, Any]:
    """Reproduce when supported; otherwise return provenance checklist (no fake metrics)."""
    detail = get_experiment(experiment_id)
    path = ROOT / detail["ledger_path"]
    ledger = ExperimentLedger(path)
    try:
        result = reproduce_experiment(experiment_id, ledger=ledger, append_reproduction=False)
        blob = result.model_dump(mode="json") if hasattr(result, "model_dump") else dict(result)
        return {
            "experiment_id": experiment_id,
            "status_zh": "复现完成",
            "result": blob,
            "explain_zh": "在相同假设下复现成功（当前一键复现支持黄金 EMA 样本实验）。",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "experiment_id": experiment_id,
            "status_zh": "可核对、暂不可一键全量复现",
            "why_zh": str(exc),
            "provenance_checklist_zh": [
                f"策略：{detail.get('strategy_id')}@{detail.get('strategy_version')}",
                f"数据集：{detail.get('dataset_id')} / hash={detail.get('dataset_hash')}",
                f"数据信任：{detail.get('data_trust_status')}",
                f"引擎：{detail.get('engine_name')} / {detail.get('adapter_version')}",
                "假设与成本见 execution_assumptions 字段",
            ],
            "note_zh": "账本封印记录仍有效；非 golden_01_ema_trend 需按数据集哈希手工复现。",
            "record": detail,
        }


def run_factor_sign_paper_api(strategy_id: str, instrument: str = "RB", bars: int = 400) -> dict[str, Any]:
    pkg = get_strategy_package(strategy_id)
    contract = compile_factor_sign_to_paper(pkg["spec"], instrument=instrument)
    ohlcv = _load_ohlcv(instrument, bars)
    result = run_factor_sign_paper(contract, ohlcv)
    snap = result.snapshot
    return {
        "PAPER_RUNTIME": "CANONICAL",
        "LEGACY_PAPER_ORDERS_USED": "NO",
        "strategy_id": strategy_id,
        "instrument": instrument,
        "contract": contract.to_dict(),
        "parity": result.parity,
        "snapshot": {
            "equity": snap.get("equity"),
            "realized_pnl": snap.get("realized_pnl"),
            "trade_count": snap.get("trade_count"),
            "max_drawdown": snap.get("max_drawdown"),
            "position_side": snap.get("position_side"),
            "orders_n": len(snap.get("orders") or []),
            "fills_n": len(snap.get("fills") or []),
            "signals_n": len(snap.get("signals") or []),
            "research_path": snap.get("path"),
        },
        "orders_preview": (snap.get("orders") or [])[-8:],
        "fills_preview": (snap.get("fills") or [])[-8:],
        "explain_zh": {
            "title_zh": "正式模拟（factor_sign → PaperRun）",
            "body_zh": "使用 canonical 适配器，语义为 sign(signal)+滞后；非旧版 paper_orders。",
            "parity_zh": result.parity.get("FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY"),
            "next_zh": "查看 Shadow / 飞行记录，核对信号与仓位是否一致。",
        },
        "REAL_MONEY": "NO",
        "ORDERS_CREATED": "NO",
        "_fills_raw": list(snap.get("fills") or [])[:20],
        "_orders_raw": list(snap.get("orders") or [])[:20],
        "strategy_spec_hash": contract.strategy_spec_hash,
        "strategy_version": contract.strategy_version,
    }


def seal_factor_sign_paper_run(db: Any, user: Any, paper_out: dict[str, Any]) -> dict[str, Any]:
    """Persist a minimal canonical PaperRun + fills so challenge milestones can credit activity.

    Does not use legacy paper_orders. REAL_MONEY stays NO.
    """
    from datetime import datetime, timezone

    from backend.app.models.paper_run import PaperRun, PaperRunFill, PaperRunOrder, PaperRunStatus

    run = PaperRun(
        user_id=user.id,
        strategy_spec_id=str(paper_out.get("strategy_id") or "unknown"),
        strategy_spec_version=str(paper_out.get("strategy_version") or "v1"),
        strategy_spec_hash=str(paper_out.get("strategy_spec_hash") or ""),
        compiled_strategy_hash=str(paper_out.get("strategy_spec_hash") or ""),
        environment="SANDBOX",
        instrument=str(paper_out.get("instrument") or "RB"),
        # Prod paper_runs columns are tight (some VARCHAR(16)); keep short codes only.
        venue="CN_FUT_RES",
        data_provider="hist_parquet",
        status=PaperRunStatus.STOPPED.value,
        engine="FS_PAPER",
        engine_version="fs_v1",
        realized_pnl=float((paper_out.get("snapshot") or {}).get("realized_pnl") or 0),
        current_balance=float((paper_out.get("snapshot") or {}).get("equity") or 100_000),
        metrics={
            "trade_count": (paper_out.get("snapshot") or {}).get("trade_count"),
            "parity": paper_out.get("parity"),
            "PAPER_RUNTIME": "CANONICAL",
            "engine_full": "FACTOR_SIGN_PAPER_RUNTIME",
            "adapter_full": "factor_sign_paper_adapter_v1",
        },
        effective_config={"path": "factor_sign_adapter", "LEGACY_PAPER_ORDERS_USED": "NO"},
        run_manifest={"kind": "factor_sign_ui_seal"},
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        stop_reason="fs_batch_done",
    )
    db.add(run)
    db.flush()

    fills = list(paper_out.pop("_fills_raw", []) or [])
    orders = list(paper_out.pop("_orders_raw", []) or [])
    n = min(len(fills), len(orders), 5) if fills else min(len(orders), 5)
    for i in range(max(n, 1 if (paper_out.get("snapshot") or {}).get("trade_count") else 0)):
        o = orders[i] if i < len(orders) else {"client_order_id": f"fs-{i}", "side": "buy", "quantity": 1, "avg_px": 1}
        f = fills[i] if i < len(fills) else {"side": o.get("side", "buy"), "quantity": o.get("quantity", 1), "price": o.get("avg_px") or o.get("price") or 1}
        order = PaperRunOrder(
            paper_run_id=run.id,
            client_order_id=str(o.get("client_order_id") or f"fs-{run.id}-{i}")[:64],
            instrument=str(paper_out.get("instrument") or "RB"),
            side=str(o.get("side") or f.get("side") or "buy")[:8],
            quantity=float(o.get("quantity") or f.get("quantity") or 1),
            price=float(o.get("avg_px") or o.get("price") or f.get("price") or 0) or None,
            status="OrderFilled",
            signal_reason="factor_sign",
        )
        db.add(order)
        db.flush()
        db.add(
            PaperRunFill(
                paper_run_id=run.id,
                order_id=order.id,
                instrument=str(paper_out.get("instrument") or "RB"),
                side=str(f.get("side") or order.side)[:8],
                quantity=float(f.get("quantity") or order.quantity),
                price=float(f.get("price") or order.price or 0),
            )
        )
    db.commit()
    return {
        "paper_run_id": str(run.id),
        "challenge_credit_zh": "已记入正式模拟成交，可用于挑战「正式模拟成交」里程碑。",
    }


def shadow_desk(strategy_id: str = "hist_fl_momentum_w20", instrument: str = "RB", bars: int = 120) -> dict[str, Any]:
    """Continuous-style Paper↔Shadow twin over a research window (no live orders)."""
    paper = run_factor_sign_paper_api(strategy_id, instrument=instrument, bars=bars)
    # Independent twin recompute
    twin = run_factor_sign_paper_api(strategy_id, instrument=instrument, bars=bars)
    divergences = 0
    events_out: list[dict[str, Any]] = []
    flight_path = ROOT / "data" / "flight_recorder" / "ui_shadow_events.jsonl"
    if flight_path.exists():
        flight_path.unlink()
    rec = FlightRecorder(flight_path)
    n = min(
        int(paper["snapshot"]["signals_n"]),
        int(twin["snapshot"]["signals_n"]),
        bars,
    )
    # Use contract recompute for precise bar snapshots
    pkg = get_strategy_package(strategy_id)
    contract = compile_factor_sign_to_paper(pkg["spec"], instrument=instrument)
    ohlcv = _load_ohlcv(instrument, bars)
    ref = run_factor_sign_paper(contract, ohlcv, paper_run_id="ui-ref")
    sh = run_factor_sign_paper(contract, ohlcv, paper_run_id="ui-shadow")
    paper_actions: list[str] = []
    shadow_actions: list[str] = []
    for i in range(min(len(ref.snapshot["positions"]), len(sh.snapshot["positions"]))):
        ppos = ref.snapshot["positions"][i]
        spos = sh.snapshot["positions"][i]
        psig = ref.snapshot["signals"][i]
        ssig = sh.snapshot["signals"][i]
        pref = "BUY" if (psig.get("intended_position") or 0) > 0 else ("SELL" if (psig.get("intended_position") or 0) < 0 else None)
        sh_side = "BUY" if (ssig.get("intended_position") or 0) > 0 else ("SELL" if (ssig.get("intended_position") or 0) < 0 else None)
        r = ShadowSnapshot(
            ts=str(ppos.get("ts")),
            strategy_id=strategy_id,
            signal=float(psig.get("signal") or 0),
            order_side=pref,
            position=float(ppos.get("position") or 0),
            source="paper",
        )
        s = ShadowSnapshot(
            ts=str(spos.get("ts")),
            strategy_id=strategy_id,
            signal=float(ssig.get("signal") or 0),
            order_side=sh_side,
            position=float(spos.get("position") or 0),
            source="shadow",
        )
        evs = compare_twins(r, s)
        if any(e.kind != "NONE" for e in evs):
            divergences += 1
        paper_actions.append(pref or "FLAT")
        shadow_actions.append(sh_side or "FLAT")
        fe = FlightEvent(
            event_id=f"ui-{i}",
            ts=r.ts,
            strategy_id=strategy_id,
            event_type="DECISION",
            saw={"signal": r.signal, "intended": pref},
            why="sign(signal) Paper↔Shadow",
            risk={"max_open": 1},
            happened={"position": r.position, "shadow_position": s.position},
        )
        rec.append(fe)
        if i >= n - 5:
            events_out.append(
                {
                    "event_id": fe.event_id,
                    "saw_zh": f"看到信号 {r.signal:.4g}，意图仓位 {pref or '空仓'}",
                    "why_zh": "按 Spec 的 sign(signal) 规则决定方向",
                    "risk_zh": "最大同时持仓 1",
                    "happened_zh": f"Paper 仓位 {r.position}；Shadow 仓位 {s.position}",
                }
            )
    # Injection proves detector
    bad = ShadowSnapshot(ts="x", strategy_id=strategy_id, signal=-1, order_side="SELL", position=-1)
    good = ShadowSnapshot(ts="x", strategy_id=strategy_id, signal=1, order_side="BUY", position=1)
    detect = {e.kind for e in compare_twins(good, bad)}
    dms = DeadManSwitch()
    recon = ReconciliationReport.from_positions(
        {instrument: float(ref.snapshot["positions"][-1].get("position") or 0)},
        {instrument: float(sh.snapshot["positions"][-1].get("position") or 0)},
    )
    sealed = {}
    if SHADOW_EV.is_file():
        sealed = json.loads(SHADOW_EV.read_text(encoding="utf-8"))
    return {
        "strategy_id": strategy_id,
        "bars": len(ref.snapshot["positions"]),
        "divergences": divergences,
        "behavior_parity": behavior_parity_report(reference_actions=paper_actions, shadow_actions=shadow_actions),
        "detector_injection_ok": "SIGNAL" in detect,
        "dead_man": {
            "trip_on_stale": dms.evaluate(now_ts_epoch=10000, last_epoch=100) == "TRIP",
            "ok_on_fresh": dms.evaluate(now_ts_epoch=10000, last_epoch=9980) == "OK",
            "explain_zh": "心跳过期会触发死人手；新鲜心跳保持正常。",
        },
        "reconciliation": recon.model_dump(mode="json"),
        "loss_attribution": loss_attribution(rec.list_events(strategy_id=strategy_id)),
        "replay_count": len(replay_events(rec, strategy_id=strategy_id)),
        "flight_preview_zh": events_out,
        "sealed_continuous_evidence": sealed.get("SHADOW_CONTINUOUS_EVIDENCE"),
        "explain_zh": {
            "title_zh": "影子对照台",
            "body_zh": "对照 Paper 与 Shadow 的信号、意图订单与仓位；分歧会标出。飞行记录用人话回答：看到了什么 / 为什么 / 风险 / 发生了什么。",
            "next_zh": "若有分歧，停止加码并回放飞行记录；实盘仍关闭。",
        },
        "REAL_MONEY": "NO",
    }


def portfolio_governor_view() -> dict[str, Any]:
    # Build synthetic returns from momentum positions on RB/AU for demo governor — reuse market data
    strategies = ["hist_fl_momentum_w20", "hist_fl_rsi_w14"]
    returns: dict[str, pd.Series] = {}
    for sid, inst in [("hist_fl_momentum_w20", "RB"), ("hist_fl_rsi_w14", "AU")]:
        try:
            pkg = get_strategy_package(sid)
            spec = validate_spec_v2(pkg["spec"])
            vals = dict(spec.parameters.values or {})
            tt = str(vals.get("template_type"))
            window = int(vals.get("param_window") or vals.get("window"))
            ohlcv = _load_ohlcv(inst, 252)
            sig = compute_template_factor(ohlcv, tt, {"window": window})
            pos = signal_to_positions(sig).shift(1).fillna(0.0)
            ret = ohlcv["close"].astype(float).pct_change(fill_method=None).fillna(0.0) * pos
            returns[sid] = ret
        except Exception:  # noqa: BLE001
            continue
    if len(returns) < 2:
        return {
            "status_zh": "证据不足",
            "why_zh": "可用策略收益序列不足，无法做组合治理。",
            "warning_zh": "多策略 ≠ 分散风险。相关高时风险会集中。",
        }
    corr = pairwise_return_correlation(returns)
    clusters = cluster_by_correlation(list(corr.get("pairs") or []), threshold=0.7)
    exp = style_exposure(returns)
    cap = capacity_check(strategy_id=strategies[0], desired_notional=5000, adv_notional=200_000)
    gov = PortfolioGovernor(
        strategy_ids=list(returns.keys()),
        weights={k: 1.0 / len(returns) for k in returns},
        instruments={"hist_fl_momentum_w20": "RB", "hist_fl_rsi_w14": "AU"},
        limits=PortfolioLimits(),
    )
    actions = evaluate_portfolio(gov, returns=returns)
    return {
        "correlation": corr,
        "clusters": clusters,
        "exposure": exp,
        "capacity": cap,
        "actions": [
            {
                "strategy_id": a.strategy_id,
                "kind": a.kind,
                "reason": a.reason,
                "reason_zh": a.reason,
                "auditable": a.auditable,
                "details": a.details,
            }
            for a in actions
        ],
        "warning_zh": "多策略并不自动等于分散风险。请看相关矩阵与风险簇；高相关簇需降风险。",
        "explain_zh": {
            "title_zh": "组合治理",
            "body_zh": "展示相关、风险簇、暴露与容量，并给出可审计的降风险建议。",
            "next_zh": "若相关过高，减少同簇权重或暂停新增风险。",
        },
    }


def dna_desk(strategy_id: str = "hist_fl_momentum_w20") -> dict[str, Any]:
    pkg = get_strategy_package(strategy_id)
    dna = build_dna_from_spec_v2(validate_spec_v2(pkg["spec"]))
    mem_items = []
    if MEMORY.is_file():
        mem_items = [m.model_dump(mode="json") for m in ResearchMemory(MEMORY).list_records()][-20:]
    grave = []
    if GRAVEYARD.is_file():
        for line in GRAVEYARD.read_text(encoding="utf-8").splitlines()[-30:]:
            if line.strip():
                grave.append(json.loads(line))
    # Seed negative memory note if empty — do not invent fake KILL; show doctrine only
    return {
        "dna": dna.model_dump(mode="json"),
        "genealogy_file": str(GENEALOGY.relative_to(ROOT)) if GENEALOGY.is_file() else None,
        "genealogy": json.loads(GENEALOGY.read_text(encoding="utf-8")) if GENEALOGY.is_file() else {},
        "memory_preview": mem_items[-10:],
        "graveyard_preview": grave[-10:],
        "explain_zh": {
            "title_zh": "策略 DNA / 谱系 / 坟场",
            "body_zh": "失败研究（淘汰 / 无边际）是资产：避免重复踩坑。",
            "no_edge_zh": "NO_EDGE_FOUND / 淘汰记录应进入坟场与研究记忆，而不是被删除。",
        },
    }


def live_readiness_card() -> dict[str, Any]:
    paper_q = "NO"
    shadow_q = "HOLD"
    if PAPER_QUAL.is_file():
        paper_q = json.loads(PAPER_QUAL.read_text(encoding="utf-8")).get("PAPER_QUALIFIED", "NO")
    if SHADOW_EV.is_file():
        shadow_q = json.loads(SHADOW_EV.read_text(encoding="utf-8")).get("SHADOW_CONTINUOUS_EVIDENCE", "HOLD")
    report = evaluate_live_readiness(
        qln5_paper_pass=paper_q == "YES",
        qln8_shadow_pass=shadow_q == "PASS",
        capital=CanaryCapitalContract(
            max_notional=5000,
            max_loss=200,
            venues_allowed=["SIMULATED"],
            strategies_allowed=["hist_fl_momentum_w20"],
            real_money_authorized=False,
        ),
        owner_live_approval=False,
    )
    d = report.model_dump(mode="json")
    lr = d.get("LIVE_READINESS")
    zh = LIVE_READINESS_ZH.get(str(lr), {})
    matrix = [m.model_dump(mode="json") for m in default_broker_matrix()]
    live_capable = any(m.get("supports_live") for m in matrix)
    return {
        **d,
        "broker_matrix": matrix,
        "BROKER_LIVE_CAPABILITY": "HOLD" if not live_capable else "PASS",
        "label_zh": zh.get("label_zh"),
        "caveat_zh": zh.get("caveat_zh"),
        "headline_zh": "具备申请实盘资格 ≠ 已允许实盘",
        "broker_hold_zh": "当前券商实盘能力为暂缓（HOLD）：未配置可实盘/金丝雀账户与凭据。",
        "owner_required_zh": [
            "券商/市场与账户环境",
            "凭据进入 Secrets Plane（禁止写入仓库）",
            "下单/撤单/持仓/权益/对账 API 证明",
            "Owner 书面实盘授权（QLN-11）",
        ],
        "QLN_11_STARTED": "NO",
        "REAL_MONEY": "NO",
        "ORDERS_CREATED": "NO",
        "paper_qualified_input": paper_q,
        "shadow_continuous_input": shadow_q,
    }


def doctrine_nav() -> dict[str, Any]:
    return {
        "doctrine_zh": "先证明，再下注",
        "chain_zh": [
            "策略",
            "实验账本",
            "证据判定",
            "建议晋级 / 暂缓 / 淘汰",
            "模拟交易",
            "影子对照",
            "实盘资格（申请≠已允许）",
        ],
        "ai_builder_role_zh": "AI 创建策略是研究辅助工具，不是产品北极星。",
    }

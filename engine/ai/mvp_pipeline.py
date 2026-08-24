"""MVP pipeline: Chinese NL → Spec → Data Gate → Nautilus → Validation → Chinese report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.ai.chinese_report import explain_backtest_zh
from engine.ai.strategy_builder import build_strategy_from_chinese, confirm_draft
from engine.data.data_gate import DataProvenance, run_data_gate, user_facing_data_gate_message
from engine.data.dataset_resolver import resolve_dataset
from engine.nautilus.availability import nautilus_available
from engine.strategies.compiler import compile_spec
from engine.strategies.lifecycle import run_validation_gate, strategy_status_card


def run_mvp_chinese_idea(
    text: str,
    *,
    confirm: bool = True,
    persist_dir: str | Path | None = None,
    run_validation: bool = True,
) -> dict[str, Any]:
    """End-to-end research path. LIVE denied. PAPER_RUNTIME denied."""
    built = build_strategy_from_chinese(text)
    out: dict[str, Any] = {
        "builder": built.to_dict(),
        "live_denied": True,
        "paper_runtime": False,
        "pipeline": ["nl", "ambiguity", "spec_draft"],
    }
    if built.draft_spec is None:
        out["status"] = "need_clarification"
        return out

    spec = built.draft_spec
    if confirm:
        spec = confirm_draft(built.draft_spec, user_approved_rules=True).canonical_dict()
        out["pipeline"].append("user_confirmation")

    try:
        compiled = compile_spec(spec)
    except Exception as exc:  # noqa: BLE001
        out["status"] = "compile_failed"
        out["error"] = str(exc)
        out["spec"] = spec
        return out

    out["compiled"] = compiled.to_dict()
    out["pipeline"].append("compile")

    instrument = str(compiled.nautilus_params.get("instrument") or spec["market"]["instrument"])
    timeframe = str(compiled.nautilus_params.get("timeframe") or spec["market"].get("timeframe") or "15m")
    dataset_ref, ohlcv = resolve_dataset(instrument, timeframe=timeframe)
    out["dataset"] = dataset_ref.to_dict()
    out["pipeline"].append("dataset_resolve")

    if not dataset_ref.available or ohlcv is None:
        out["status"] = "no_data"
        out["report_zh"] = {
            "verdict_zh": dataset_ref.message_zh,
            "bullets_zh": ["导入数据", "选择其他数据源", "更换品种"],
            "next_step_zh": "先解决数据问题，再运行回测。",
            "disclaimer_zh": "没有数据时不会伪造回测结果。",
        }
        out["spec"] = spec
        return out

    gate = run_data_gate(
        ohlcv,
        provenance=DataProvenance(
            provider=dataset_ref.provider,
            broker=dataset_ref.broker,
            venue=dataset_ref.venue,
            symbol=dataset_ref.instrument,
            instrument=dataset_ref.instrument,
            timezone="UTC",
            frequency=timeframe,
            broker_specific=dataset_ref.broker_specific,
        ),
        timeframe=timeframe,
        require_broker_specific=False,
    )
    out["data_gate"] = gate.to_dict()
    out["data_gate_user"] = user_facing_data_gate_message(gate)
    out["pipeline"].append("data_gate")
    if gate.status == "FAIL":
        out["status"] = "data_gate_failed"
        out["spec"] = spec
        out["report_zh"] = {
            "verdict_zh": out["data_gate_user"]["title_zh"],
            "bullets_zh": gate.issues_zh,
            "next_step_zh": out["data_gate_user"]["body_zh"],
            "disclaimer_zh": "底层技术证据已保留在 data_gate.issues_tech。",
        }
        return out

    if not nautilus_available():
        out["status"] = "nautilus_unavailable"
        out["spec"] = spec
        return out

    from engine.nautilus.backtest_adapter import NautilusBacktestAdapter

    adapter = NautilusBacktestAdapter(require_pinned=True)
    # Prefer instrument-aware runner when available
    run_fn = getattr(adapter, "run_ema_for_instrument", None)
    if callable(run_fn):
        result = run_fn(
            instrument=dataset_ref.instrument,
            ohlcv=ohlcv,
            fast_ema=int(compiled.nautilus_params.get("fast_ema", 10)),
            slow_ema=int(compiled.nautilus_params.get("slow_ema", 20)),
            trade_size=str(compiled.nautilus_params.get("trade_size", "1000000")),
            strategy_id=spec["strategy"]["id"],
            strategy_version=spec["strategy"]["version"],
            persist_dir=persist_dir,
        )
    else:
        result = adapter.run_compiled_ema(
            compiled.nautilus_params,
            ohlcv=ohlcv if dataset_ref.instrument == "EUR/USD" else None,
            strategy_id=spec["strategy"]["id"],
            strategy_version=spec["strategy"]["version"],
            persist_dir=persist_dir,
        )

    out["pipeline"].extend(["nautilus_backtest", "chinese_report"])
    out["backtest"] = result.to_dict()
    report = explain_backtest_zh(
        metrics=result.metrics,
        strategy_name=spec["strategy"]["name"],
        fill_count=result.fill_count,
        ambiguous=bool(spec["strategy"].get("ambiguous")),
    )
    out["report_zh"] = report

    validation = None
    if run_validation and result.status == "success":
        validation = run_validation_gate(spec, ohlcv)
        out["validation_gate"] = validation.to_dict()
        out["pipeline"].append("validation_gate")
        out["status_card"] = strategy_status_card(
            name=spec["strategy"]["name"],
            lifecycle=validation.lifecycle,
            data_gate_status=gate.status,
            validation=validation,
            max_drawdown=(result.metrics or {}).get("max_drawdown"),
            ai_verdict_zh=report.get("verdict_zh", ""),
        )

    out["status"] = "ok" if result.status == "success" else "backtest_failed"
    out["spec"] = spec
    out["paper_ready"] = bool(validation.paper_ready) if validation else False
    return out

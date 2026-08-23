"""MVP pipeline: Chinese NL → Spec → compile → Nautilus backtest → Chinese report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.ai.chinese_report import explain_backtest_zh
from engine.ai.strategy_builder import build_strategy_from_chinese, confirm_draft
from engine.nautilus.availability import nautilus_available
from engine.strategies.compiler import compile_spec


def run_mvp_chinese_idea(
    text: str,
    *,
    confirm: bool = True,
    persist_dir: str | Path | None = None,
) -> dict[str, Any]:
    """End-to-end research path. LIVE is always denied."""
    built = build_strategy_from_chinese(text)
    out: dict[str, Any] = {
        "builder": built.to_dict(),
        "live_denied": True,
        "pipeline": ["nl", "ambiguity", "spec_draft"],
    }
    if built.draft_spec is None:
        out["status"] = "need_clarification"
        return out

    spec = built.draft_spec
    if confirm:
        # Confirming rules still keeps LIVE denied; assumed values keep ambiguous=true
        spec = confirm_draft(built.draft_spec, user_approved_rules=True).canonical_dict()
        out["pipeline"].append("user_confirmation")

    # Compiler currently supports ema_cross on EUR/USD golden path.
    # For non-EUR drafts, still compile params but run golden EUR data only when
    # instrument maps to EUR/USD; otherwise return spec-only research package.
    try:
        compiled = compile_spec(spec)
    except Exception as exc:  # noqa: BLE001
        out["status"] = "compile_failed"
        out["error"] = str(exc)
        out["spec"] = spec
        return out

    out["compiled"] = compiled.to_dict()
    out["pipeline"].append("compile")

    instrument = compiled.nautilus_params.get("instrument")
    if instrument != "EUR/USD" or not nautilus_available():
        report = explain_backtest_zh(
            metrics={"fill_count": 0},
            strategy_name=spec["strategy"]["name"],
            fill_count=0,
            ambiguous=bool(spec["strategy"].get("ambiguous")),
        )
        out["status"] = "spec_ready_awaiting_matching_data"
        out["report_zh"] = report
        out["spec"] = spec
        return out

    from engine.nautilus.backtest_adapter import NautilusBacktestAdapter

    adapter = NautilusBacktestAdapter(require_pinned=True)
    result = adapter.run_compiled_ema(
        compiled.nautilus_params,
        strategy_id=spec["strategy"]["id"],
        strategy_version=spec["strategy"]["version"],
        persist_dir=persist_dir,
    )
    out["pipeline"].extend(["nautilus_backtest", "chinese_report"])
    out["backtest"] = result.to_dict()
    out["report_zh"] = explain_backtest_zh(
        metrics=result.metrics,
        strategy_name=spec["strategy"]["name"],
        fill_count=result.fill_count,
        ambiguous=bool(spec["strategy"].get("ambiguous")),
    )
    out["status"] = "ok" if result.status == "success" else "backtest_failed"
    out["spec"] = spec
    return out

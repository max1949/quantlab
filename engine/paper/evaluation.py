"""Paper run evaluation → research feedback (Phase 6 minimal loop)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EvaluationStatus = Literal[
    "COMPLETE",
    "INSUFFICIENT_EVIDENCE",
    "FAILED",
    "RUNNING",
]


@dataclass
class PaperEvaluation:
    strategy_spec_id: str
    strategy_spec_version: str
    paper_run_id: str
    backtest_run_id: str | None = None
    performance_summary: dict[str, Any] = field(default_factory=dict)
    comparison_summary: dict[str, Any] = field(default_factory=dict)
    parity_status: str = "INVALID_COMPARISON"
    risk_events: list[dict[str, Any]] = field(default_factory=list)
    runtime_errors: list[str] = field(default_factory=list)
    data_quality_events: list[str] = field(default_factory=list)
    evaluation_status: EvaluationStatus = "INSUFFICIENT_EVIDENCE"
    research_feedback_zh: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_paper_evaluation(
    *,
    strategy_spec_id: str,
    strategy_spec_version: str,
    paper_run_id: str,
    performance_summary: dict[str, Any],
    comparison: dict[str, Any],
    parity_status: str,
    run_status: str,
    failure_reason: str = "",
    risk_events: list[dict[str, Any]] | None = None,
    data_stale: bool = False,
    backtest_run_id: str | None = None,
) -> PaperEvaluation:
    trade_count = int(performance_summary.get("trade_count") or 0)
    duration = float(performance_summary.get("duration_seconds") or 0)

    runtime_errors: list[str] = []
    if failure_reason:
        runtime_errors.append(failure_reason)

    data_events: list[str] = []
    if data_stale:
        data_events.append("DATA_STALE detected during run")

    if run_status in {"FAILED", "KILLED"}:
        status: EvaluationStatus = "FAILED"
    elif run_status in {"RUNNING", "STARTING"}:
        status = "RUNNING"
    elif trade_count < 1 or duration < 30:
        status = "INSUFFICIENT_EVIDENCE"
    else:
        status = "COMPLETE"

    feedback: list[str] = []
    feedback.append(
        f"策略 {strategy_spec_id}@{strategy_spec_version} 模拟运行状态：{run_status}。"
    )
    if performance_summary:
        feedback.append(
            f"模拟净盈亏 {performance_summary.get('net_pnl', 0):+.2f}，"
            f"最大回撤 {float(performance_summary.get('max_drawdown', 0)) * 100:.2f}%，"
            f"成交 {trade_count} 笔。"
        )
    if parity_status == "CONSISTENT":
        feedback.append("回测与模拟信号/盈亏大致一致，可继续观察 Paper 样本。")
    elif parity_status == "EXPECTED_EXECUTION_DRIFT":
        feedback.append("存在预期内的执行差异（滑点/延迟），策略定义一致。")
    elif parity_status == "MATERIAL_DRIFT":
        feedback.append("回测与模拟出现显著漂移，建议回到研究阶段复核 Spec 与数据。")
    else:
        feedback.append("缺少有效回测基线，暂无法比较漂移。")
    if status == "INSUFFICIENT_EVIDENCE":
        feedback.append("Paper 样本不足 — 不能据此判定策略有效或无效。")

    return PaperEvaluation(
        strategy_spec_id=strategy_spec_id,
        strategy_spec_version=strategy_spec_version,
        paper_run_id=paper_run_id,
        backtest_run_id=backtest_run_id,
        performance_summary=performance_summary,
        comparison_summary=comparison,
        parity_status=parity_status,
        risk_events=list(risk_events or []),
        runtime_errors=runtime_errors,
        data_quality_events=data_events,
        evaluation_status=status,
        research_feedback_zh=feedback,
    )

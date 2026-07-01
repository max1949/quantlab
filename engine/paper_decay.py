"""纸面跟踪衰减评估 — 对比验证期基准与近期纸面表现。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperDecayVerdict:
    status: str  # ok | watch | alert
    reasons: list[str]
    baseline_sharpe: float | None
    paper_sharpe: float | None
    baseline_max_dd: float | None
    paper_max_dd: float | None
    nav_change_pct: float | None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "reasons": self.reasons,
            "baseline_sharpe": self.baseline_sharpe,
            "paper_sharpe": self.paper_sharpe,
            "baseline_max_dd": self.baseline_max_dd,
            "paper_max_dd": self.paper_max_dd,
            "nav_change_pct": self.nav_change_pct,
        }


def assess_paper_decay(
    *,
    validation_oos: dict | None,
    paper_metrics: dict | None,
    nav_series: list[float] | None = None,
    sharpe_drop_alert: float = 0.35,
    sharpe_drop_watch: float = 0.2,
    dd_worsen_alert: float = 0.08,
    dd_worsen_watch: float = 0.04,
    nav_drawdown_alert: float = -0.08,
) -> PaperDecayVerdict:
    """对比 OOS 基准与纸面指标, 输出 ok/watch/alert。"""
    reasons: list[str] = []
    status = "ok"

    oos = validation_oos or {}
    paper = paper_metrics or {}
    base_sharpe = _metric(oos.get("out_of_sample", {}), "sharpe")
    if base_sharpe is None:
        base_sharpe = _metric(oos, "sharpe")
    paper_sharpe = _metric(paper, "sharpe")
    base_dd = _metric(oos.get("out_of_sample", {}), "max_drawdown")
    if base_dd is None:
        base_dd = _metric(oos, "max_drawdown")
    paper_dd = _metric(paper, "max_drawdown")

    if base_sharpe is not None and paper_sharpe is not None:
        drop = base_sharpe - paper_sharpe
        if drop >= sharpe_drop_alert:
            status = "alert"
            reasons.append(f"纸面夏普较验证样本外下降 {drop:.2f}")
        elif drop >= sharpe_drop_watch:
            status = _raise_status(status, "watch")
            reasons.append(f"纸面夏普较验证样本外走弱 {drop:.2f}")

    if base_dd is not None and paper_dd is not None:
        # max_drawdown 通常为负数, 更差 = 更负
        worsen = abs(paper_dd) - abs(base_dd)
        if worsen >= dd_worsen_alert:
            status = "alert"
            reasons.append(f"纸面最大回撤较验证期加深 {worsen * 100:.1f}%")
        elif worsen >= dd_worsen_watch:
            status = _raise_status(status, "watch")
            reasons.append(f"纸面回撤较验证期有所扩大")

    nav_change = None
    if nav_series and len(nav_series) >= 2:
        start, end = nav_series[0], nav_series[-1]
        if start and start > 0:
            nav_change = (end - start) / start
            if nav_change <= nav_drawdown_alert:
                status = "alert"
                reasons.append(f"近期纸面净值回撤 {nav_change * 100:.1f}%")

    if status == "ok" and paper_sharpe is not None and paper_sharpe < 0:
        status = "watch"
        reasons.append("纸面夏普为负, 建议复查因子逻辑")

    return PaperDecayVerdict(
        status=status,
        reasons=reasons,
        baseline_sharpe=base_sharpe,
        paper_sharpe=paper_sharpe,
        baseline_max_dd=base_dd,
        paper_max_dd=paper_dd,
        nav_change_pct=nav_change,
    )


def _f(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _metric(d: dict, key: str) -> float | None:
    if not d:
        return None
    v = _f(d.get(key))
    if v is not None:
        return v
    if key == "sharpe":
        return _f(d.get("sharpe_ratio"))
    return None


def _raise_status(current: str, new: str) -> str:
    order = {"ok": 0, "watch": 1, "alert": 2}
    return new if order.get(new, 0) > order.get(current, 0) else current

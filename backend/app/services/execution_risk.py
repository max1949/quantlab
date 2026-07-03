"""机构级执行风控预检。"""

from __future__ import annotations

from backend.app.core.config import get_settings
from engine.execution_adapter import CHANNEL_QMT, CHANNEL_VNPY


class RiskBlockedError(Exception):
    def __init__(self, message: str, *, verdict: str = "blocked", detail: str = "") -> None:
        super().__init__(message)
        self.verdict = verdict
        self.detail = detail


def preflight(
    *,
    notional_cny: float,
    channel: str,
    regime_fit_score: int | None = None,
    acknowledge_risk: bool = False,
) -> dict:
    """下单前风控检查; 不通过抛 RiskBlockedError。"""
    s = get_settings()
    reasons: list[str] = []

    if s.execution_kill_switch:
        reasons.append("执行总闸已关闭 (kill switch)")

    if notional_cny > s.execution_max_notional_cny:
        reasons.append(
            f"名义金额 {notional_cny:.0f} 超过单笔上限 {s.execution_max_notional_cny:.0f}"
        )

    if channel in (CHANNEL_VNPY, CHANNEL_QMT):
        min_fit = s.execution_min_regime_fit_vnpy
        if regime_fit_score is not None and regime_fit_score < min_fit and not acknowledge_risk:
            reasons.append(
                f"制度×策略适配分 {regime_fit_score} 低于网关通道门槛 {min_fit}"
            )

    if reasons:
        detail = "; ".join(reasons)
        raise RiskBlockedError(detail, verdict="blocked", detail=detail)

    return {"verdict": "passed", "detail": ""}

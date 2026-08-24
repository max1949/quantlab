"""EMA signal evaluation for paper sandbox (from frozen effective config)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class SignalDecision:
    instrument: str
    timestamp: str
    strategy_version: str
    decision: str  # BUY | SELL | HOLD | EXIT
    reason: str
    conditions: list[str] = field(default_factory=list)
    condition_values: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "instrument": self.instrument,
            "timestamp": self.timestamp,
            "strategy_version": self.strategy_version,
            "decision": self.decision,
            "reason": self.reason,
            "conditions": self.conditions,
            "condition_values": self.condition_values,
        }


@dataclass
class EmaSignalEngine:
    fast: int = 10
    slow: int = 20
    adx_threshold: float = 25.0
    strategy_version: str = "v1"
    _prices: deque[float] = field(default_factory=lambda: deque(maxlen=500))
    _position_side: str | None = None

    def update(self, price: float, *, timestamp: str, instrument: str) -> SignalDecision:
        self._prices.append(price)
        if len(self._prices) < self.slow:
            return SignalDecision(
                instrument=instrument,
                timestamp=timestamp,
                strategy_version=self.strategy_version,
                decision="HOLD",
                reason="预热中",
                conditions=[],
                condition_values={"price": price},
            )

        prices = list(self._prices)
        ema_f = _ema(prices, self.fast)
        ema_s = _ema(prices, self.slow)
        adx = _pseudo_adx(prices)

        cond_vals = {"EMA20": ema_f, "EMA60": ema_s, "ADX": adx, "price": price}
        rules: list[str] = []
        decision = "HOLD"
        reason = "条件未满足"

        if ema_f > ema_s and adx > self.adx_threshold:
            rules = ["EMA20 > EMA60", f"ADX > {self.adx_threshold:.0f}"]
            if self._position_side == "long":
                decision = "HOLD"
                reason = "已持有多单"
            else:
                decision = "BUY"
                reason = "趋势多头"
        elif ema_f < ema_s and adx > self.adx_threshold:
            rules = ["EMA20 < EMA60", f"ADX > {self.adx_threshold:.0f}"]
            if self._position_side == "short":
                decision = "HOLD"
                reason = "已持有空单"
            else:
                decision = "SELL"
                reason = "趋势空头"
        elif self._position_side:
            decision = "EXIT"
            reason = "趋势减弱或反向"

        return SignalDecision(
            instrument=instrument,
            timestamp=timestamp,
            strategy_version=self.strategy_version,
            decision=decision,
            reason=reason,
            conditions=rules,
            condition_values=cond_vals,
        )

    def set_position(self, side: str | None) -> None:
        self._position_side = side


def _ema(prices: list[float], span: int) -> float:
    if not prices:
        return 0.0
    k = 2 / (span + 1)
    val = prices[0]
    for p in prices[1:]:
        val = p * k + val * (1 - k)
    return val


def _pseudo_adx(prices: list[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 0.0
    moves = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
    return sum(moves[-period:]) / period / max(prices[-1], 1e-9) * 10_000

"""Frozen fee / slippage / execution assumptions for experiments."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from engine.experiment.errors import ExperimentError


class ExecutionAssumptions(BaseModel):
    fee_model: str = "turnover_fee_rate"
    fee_rate: float = 0.0005
    slippage_model: str = "turnover_bps"
    slippage_bps: float = 1.0
    latency_assumption: str = "zero_bar_close"
    fill_model: str = "next_bar_open_or_close_mark"
    order_type: str = "MARKET"
    time_in_force: str = "GTC"
    notes: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def per_turnover_cost(self) -> float:
        return float(self.fee_rate) + float(self.slippage_bps) / 1e4


def validate_execution_assumptions(data: ExecutionAssumptions | dict[str, Any]) -> ExecutionAssumptions:
    if isinstance(data, dict):
        try:
            data = ExecutionAssumptions.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            raise ExperimentError(f"invalid execution assumptions: {exc}") from exc
    if data.fee_rate < 0 or data.slippage_bps < 0:
        raise ExperimentError("fee_rate and slippage_bps must be >= 0")
    return data


class CostAttribution(BaseModel):
    """Research cost attribution — not broker P&L."""

    compute_units: float = 0.0
    market_data_units: float = 0.0
    ai_tokens: float = 0.0
    currency: str = "USD"
    estimated_cost: float = 0.0
    notes: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

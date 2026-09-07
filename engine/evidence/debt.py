"""Research Debt — accumulates when evidence is thin, stressed, or overfit-prone."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ResearchDebt:
    score: float
    items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_research_debt(
    *,
    gates: dict[str, str],
    overfit_risk: str,
    trade_count: int,
    periods: int,
    min_trades: int,
    min_periods: int,
) -> ResearchDebt:
    debt = 0.0
    items: list[str] = []
    for name, flag in gates.items():
        if flag == "FAIL":
            debt += 20.0
            items.append(f"gate_fail:{name}")
        elif flag == "INSUFFICIENT":
            debt += 8.0
            items.append(f"gate_insufficient:{name}")
    if overfit_risk == "HIGH":
        debt += 25.0
        items.append("overfit_high")
    elif overfit_risk == "MEDIUM":
        debt += 10.0
        items.append("overfit_medium")
    if trade_count < min_trades:
        debt += 15.0
        items.append(f"low_trades:{trade_count}<{min_trades}")
    if periods < min_periods:
        debt += 10.0
        items.append(f"short_history:{periods}<{min_periods}")
    return ResearchDebt(score=min(100.0, debt), items=items)

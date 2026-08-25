"""Strategy Validation Gate — research evidence, not product features.

Final outcomes: PROMOTE | HOLD | REJECT.
Promotion is never automatic from a profitable backtest alone.
LIVE / Phase 7 remain DENY.
"""

from engine.validation.decision import Decision, OverfitRisk, decide_outcome
from engine.validation.pipeline import StrategyValidationReport, validate_candidate

__all__ = [
    "Decision",
    "OverfitRisk",
    "StrategyValidationReport",
    "decide_outcome",
    "validate_candidate",
]

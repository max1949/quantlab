"""Map Evidence decisions → Research Memory outcomes (QLN-6)."""

from __future__ import annotations

from typing import Any

from engine.strategy_dna.memory import Outcome


def evidence_decision_to_memory_outcome(decision: str) -> Outcome:
    """Canonical mapping. KILL is recorded as NO_EDGE_FOUND for research memory."""
    d = (decision or "").strip().upper()
    if d == "KILL":
        return "NO_EDGE_FOUND"
    if d == "PROMOTE":
        return "PROMOTE"
    if d == "HOLD":
        return "HOLD"
    if d == "NO_EDGE_FOUND":
        return "NO_EDGE_FOUND"
    if d == "INSUFFICIENT":
        return "INSUFFICIENT"
    return "INSUFFICIENT"


def is_negative_outcome(outcome: Outcome | str) -> bool:
    return str(outcome) in ("KILL", "NO_EDGE_FOUND")


def forbid_continue_optimize_payload(outcome: Outcome | str) -> dict[str, Any]:
    """Acceptance contract: negative outcomes must not recommend '继续优化'."""
    if is_negative_outcome(outcome):
        return {
            "recommendation": "STOP_OR_ARCHIVE",
            "continue_optimize": False,
            "message": "NO_EDGE_FOUND — do not optimize until pass; archive / graveyard.",
        }
    return {
        "recommendation": "HOLD_OR_PROMOTE_PATH",
        "continue_optimize": False,
        "message": "Follow Evidence decision; threshold relaxation forbidden.",
    }

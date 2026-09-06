"""Strategy default semantics — EXAMPLE ≠ DEFAULT (QLN-1)."""

from __future__ import annotations

# Official Spec/compiler/golden defaults for ema_cross when Spec omits params.
CANONICAL_EMA_DEFAULT_FAST = 10
CANONICAL_EMA_DEFAULT_SLOW = 20

# UX copy often shows EMA20/EMA60 as teaching examples — not canonical defaults.
EXAMPLE_EMA_FAST = 20
EXAMPLE_EMA_SLOW = 60

EXAMPLE_IS_NOT_DEFAULT = True
STRATEGY_DEFAULT_SEMANTICS = "ONE_CANONICAL_SOURCE"


def assert_example_not_default() -> None:
    if (EXAMPLE_EMA_FAST, EXAMPLE_EMA_SLOW) == (
        CANONICAL_EMA_DEFAULT_FAST,
        CANONICAL_EMA_DEFAULT_SLOW,
    ):
        raise AssertionError("example EMA periods must remain distinct from canonical defaults")
    if not EXAMPLE_IS_NOT_DEFAULT:
        raise AssertionError("EXAMPLE_IS_NOT_DEFAULT must be True")
    if STRATEGY_DEFAULT_SEMANTICS != "ONE_CANONICAL_SOURCE":
        raise AssertionError("strategy defaults must have one canonical source (Strategy Spec)")


def format_ema_label(period: int) -> str:
    """Runtime/display label must reflect actual period, not hardcoded EMA20/EMA60."""
    return f"EMA{int(period)}"

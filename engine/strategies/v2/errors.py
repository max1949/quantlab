"""QLN-2 Strategy Spec v2 errors — fail closed."""

from __future__ import annotations


class SpecV2Error(ValueError):
    """Invalid Spec v2 / Contract / Package — never silently default around."""

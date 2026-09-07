"""QLN-3 experiment errors — fail closed."""

from __future__ import annotations


class ExperimentError(ValueError):
    """Invalid experiment / ledger / trust gate failure."""


class ReproduceError(ExperimentError):
    """Reproduction failed or drifted beyond pre-declared tolerance."""

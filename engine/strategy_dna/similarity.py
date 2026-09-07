"""Duplicate / similarity detection on Strategy DNA fingerprints."""

from __future__ import annotations

from engine.strategy_dna.dna import StrategyDNA


def dna_similarity(a: StrategyDNA, b: StrategyDNA) -> dict[str, bool | float]:
    same_family = a.family_id == b.family_id
    same_signals = a.signal_kinds == b.signal_kinds
    same_params = a.param_fingerprint == b.param_fingerprint
    same_universe = a.universe_fingerprint == b.universe_fingerprint
    score = (
        0.4 * float(same_signals)
        + 0.3 * float(same_params)
        + 0.2 * float(same_universe)
        + 0.1 * float(same_family)
    )
    return {
        "same_family": same_family,
        "same_signals": same_signals,
        "same_params": same_params,
        "same_universe": same_universe,
        "similarity_score": score,
        "near_duplicate": bool(same_signals and same_params),
    }

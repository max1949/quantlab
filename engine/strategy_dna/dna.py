"""Strategy DNA — compact fingerprint of strategy research identity (QLN-6)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from engine.domain.hashing import HashKind, compute_hash
from engine.strategies.v2.spec_v2 import StrategySpecV2


class StrategyDNA(BaseModel):
    strategy_id: str
    version: str
    family_id: str
    signal_kinds: list[str] = Field(default_factory=list)
    param_fingerprint: str = ""
    universe_fingerprint: str = ""
    risk_fingerprint: str = ""
    execution_fingerprint: str = ""
    content_hash: str = ""
    origin: str = ""  # historical_reconstruction | new_research | imported
    tags: list[str] = Field(default_factory=list)

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def build_dna_from_spec_v2(
    spec: StrategySpecV2,
    *,
    origin: str = "unknown",
) -> StrategyDNA:
    signal_kinds = sorted(
        {
            c.type
            for c in (
                list(spec.signal_logic.entry_long)
                + list(spec.signal_logic.entry_short)
                + list(spec.signal_logic.exit)
            )
        }
    )
    param_fp = compute_hash(HashKind.CONFIG, spec.parameters.values)
    uni_fp = compute_hash(
        HashKind.CONFIG,
        {"instruments": spec.universe.instruments, "tf": spec.timeframe.timeframe},
    )
    risk_fp = compute_hash(HashKind.CONFIG, spec.risk.model_dump(mode="json"))
    exec_fp = compute_hash(HashKind.CONFIG, spec.execution.model_dump(mode="json"))
    dna = StrategyDNA(
        strategy_id=spec.identity.strategy_id,
        version=spec.identity.version,
        family_id=spec.identity.family_id or spec.identity.strategy_id,
        signal_kinds=signal_kinds,
        param_fingerprint=param_fp,
        universe_fingerprint=uni_fp,
        risk_fingerprint=risk_fp,
        execution_fingerprint=exec_fp,
        content_hash=spec.content_hash(),
        origin=origin,
        tags=list(spec.metadata.tags),
    )
    return dna

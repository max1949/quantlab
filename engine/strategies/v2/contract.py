"""Strategy Contract — WHAT/WHY/WHEN/RISK/INVALIDATION (QLN-2 defines contract only)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from engine.strategies.v2.errors import SpecV2Error


class StrategyContract(BaseModel):
    contract_id: str
    strategy_id: str
    version: str
    what: str
    why: str
    when: list[str] = Field(default_factory=list)
    when_not: list[str] = Field(default_factory=list)
    risk: str
    invalidation: list[str] = Field(default_factory=list)
    expected: list[str] = Field(default_factory=list)
    abnormal: list[str] = Field(default_factory=list)
    retirement: list[str] = Field(default_factory=list)
    schema_version: str = "2.0"

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def validate_contract(data: dict[str, Any] | StrategyContract) -> StrategyContract:
    if isinstance(data, StrategyContract):
        c = data
    else:
        try:
            c = StrategyContract.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            raise SpecV2Error(f"invalid strategy contract: {exc}") from exc
    required = {
        "contract_id": c.contract_id,
        "strategy_id": c.strategy_id,
        "version": c.version,
        "what": c.what,
        "why": c.why,
        "risk": c.risk,
    }
    for k, v in required.items():
        if not str(v).strip():
            raise SpecV2Error(f"strategy contract missing required field: {k}")
    if not c.when:
        raise SpecV2Error("strategy contract.when must be non-empty")
    if not c.when_not:
        raise SpecV2Error("strategy contract.when_not must be non-empty")
    if not c.invalidation:
        raise SpecV2Error("strategy contract.invalidation must be non-empty")
    return c

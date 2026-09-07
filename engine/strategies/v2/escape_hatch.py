"""Code Escape Hatch Contract — custom components without bypassing Contract/Invariants."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.secrets import assert_no_secrets


class CustomComponentDecl(BaseModel):
    name: str
    language: Literal["python", "rust"]
    entrypoint: str
    content_hash: str
    capabilities: list[str] = Field(default_factory=list)
    version: str = "0.1.0"
    description: str = ""

    @field_validator("content_hash")
    @classmethod
    def _hash_shape(cls, v: str) -> str:
        if not v or len(v) < 16:
            raise ValueError("content_hash required (min 16 chars)")
        return v

    @field_validator("capabilities")
    @classmethod
    def _caps(cls, v: list[str]) -> list[str]:
        allowed = {
            "signal",
            "filter",
            "sizing",
            "risk_check",
            "execution_hint",
            "indicator",
        }
        for c in v:
            if c not in allowed:
                raise ValueError(f"unsupported capability: {c}")
        return v


class CodeEscapeHatch(BaseModel):
    """Boundary: custom code may extend, never override Contract / Invariants."""

    enabled: bool = False
    components: list[CustomComponentDecl] = Field(default_factory=list)
    must_respect_contract: bool = True
    must_respect_invariants: bool = True
    secrets_forbidden: bool = True
    notes: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def validate_escape_hatch(data: dict[str, Any] | CodeEscapeHatch) -> CodeEscapeHatch:
    if isinstance(data, CodeEscapeHatch):
        hatch = data
    else:
        try:
            hatch = CodeEscapeHatch.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            raise SpecV2Error(f"malformed custom component declaration: {exc}") from exc
    if not hatch.must_respect_contract or not hatch.must_respect_invariants:
        raise SpecV2Error("escape hatch cannot disable Contract/Invariants respect flags")
    if not hatch.secrets_forbidden:
        raise SpecV2Error("escape hatch must keep secrets_forbidden=true")
    if hatch.enabled and not hatch.components:
        raise SpecV2Error("enabled escape hatch requires at least one component")
    assert_no_secrets(hatch.canonical_dict())
    return hatch

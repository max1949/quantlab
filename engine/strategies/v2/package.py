"""Portable Strategy Package — export/import deterministic, no secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from engine.domain.hashing import HashKind, canonical_json_bytes, compute_hash
from engine.strategies.v2.contract import StrategyContract, validate_contract
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.escape_hatch import CodeEscapeHatch, validate_escape_hatch
from engine.strategies.v2.invariants import StrategyInvariants, validate_invariants
from engine.strategies.v2.lineage import LineageRecord
from engine.strategies.v2.secrets import assert_no_secrets, find_secrets
from engine.strategies.v2.spec_v2 import StrategySpecV2, validate_spec_v2


PACKAGE_FORMAT = "quantlab.strategy_package"
PACKAGE_FORMAT_VERSION = "1.0"


class PackageManifest(BaseModel):
    format: str = PACKAGE_FORMAT
    format_version: str = PACKAGE_FORMAT_VERSION
    strategy_id: str
    version: str
    content_hash: str
    files: list[str] = Field(default_factory=list)


class StrategyPackage(BaseModel):
    manifest: PackageManifest
    strategy_spec: StrategySpecV2
    strategy_contract: StrategyContract
    invariants: StrategyInvariants
    parameters: dict[str, Any] = Field(default_factory=dict)
    data_requirements: dict[str, Any] = Field(default_factory=dict)
    lineage: LineageRecord | None = None
    escape_hatch: CodeEscapeHatch | None = None
    readme: str = ""

    def hash_payload(self) -> dict[str, Any]:
        """Payload used for content hash — excludes README prose only."""
        return {
            "format": PACKAGE_FORMAT,
            "format_version": PACKAGE_FORMAT_VERSION,
            "strategy_spec": self.strategy_spec.canonical_dict(),
            "strategy_contract": self.strategy_contract.canonical_dict(),
            "invariants": self.invariants.canonical_dict(),
            "parameters": self.parameters,
            "data_requirements": self.data_requirements,
            "lineage": self.lineage.canonical_dict() if self.lineage else None,
            "escape_hatch": self.escape_hatch.canonical_dict() if self.escape_hatch else None,
        }

    def compute_hash(self) -> str:
        return compute_hash(HashKind.ARTIFACT, self.hash_payload())

    def to_export_dict(self) -> dict[str, Any]:
        h = self.compute_hash()
        files = [
            "manifest.json",
            "strategy_spec.json",
            "strategy_contract.json",
            "invariants.json",
            "parameters.json",
            "data_requirements.json",
            "lineage.json",
            "README.md",
        ]
        if self.escape_hatch is not None:
            files.append("escape_hatch.json")
        manifest = PackageManifest(
            strategy_id=self.strategy_spec.identity.strategy_id,
            version=self.strategy_spec.identity.version,
            content_hash=h,
            files=sorted(files),
        )
        return {
            "manifest": manifest.model_dump(mode="json"),
            "strategy_spec": self.strategy_spec.canonical_dict(),
            "strategy_contract": self.strategy_contract.canonical_dict(),
            "invariants": self.invariants.canonical_dict(),
            "parameters": self.parameters,
            "data_requirements": self.data_requirements,
            "lineage": self.lineage.canonical_dict() if self.lineage else None,
            "escape_hatch": self.escape_hatch.canonical_dict() if self.escape_hatch else None,
            "readme": self.readme,
        }


def build_package(
    *,
    spec: StrategySpecV2,
    contract: StrategyContract,
    invariants: StrategyInvariants,
    lineage: LineageRecord | None = None,
    escape_hatch: CodeEscapeHatch | None = None,
    readme: str = "",
) -> StrategyPackage:
    validate_spec_v2(spec)
    validate_contract(contract)
    validate_invariants(invariants)
    if escape_hatch is not None:
        validate_escape_hatch(escape_hatch)
    if contract.strategy_id != spec.identity.strategy_id:
        raise SpecV2Error("contract.strategy_id must match spec identity")
    if invariants.strategy_id != spec.identity.strategy_id:
        raise SpecV2Error("invariants.strategy_id must match spec identity")
    pkg = StrategyPackage(
        manifest=PackageManifest(
            strategy_id=spec.identity.strategy_id,
            version=spec.identity.version,
            content_hash="",  # filled on export
            files=[],
        ),
        strategy_spec=spec,
        strategy_contract=contract,
        invariants=invariants,
        parameters=dict(spec.parameters.values),
        data_requirements=spec.data_requirements.model_dump(mode="json"),
        lineage=lineage,
        escape_hatch=escape_hatch,
        readme=readme or f"# {spec.identity.name}\n\n{spec.metadata.description}\n",
    )
    assert_no_secrets(pkg.to_export_dict())
    violations = invariants.check_spec(
        risk=spec.risk.model_dump(mode="json"),
        stop_type=spec.stop_loss.type,
    )
    deny_ids = {r.id for r in invariants.rules if r.severity == "deny"}
    hard = [v for v in violations if any(v.startswith(i) for i in deny_ids)]
    if hard:
        raise SpecV2Error(f"invariant violations: {hard}")
    return pkg


def export_package(pkg: StrategyPackage, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = pkg.to_export_dict()
    assert_no_secrets(data)
    # Ensure canonical encoding path is exercised (hash already uses it)
    _ = canonical_json_bytes(data)
    # Pretty for humans; hash is independent of pretty formatting
    p.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def import_package(path: str | Path) -> StrategyPackage:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SpecV2Error("package root must be object")
    assert_no_secrets(raw)
    manifest = raw.get("manifest") or {}
    if manifest.get("format") != PACKAGE_FORMAT:
        raise SpecV2Error("unknown package format")
    expected = manifest.get("content_hash")
    if not expected:
        raise SpecV2Error("manifest.content_hash required")

    lineage_raw = raw.get("lineage")
    escape_raw = raw.get("escape_hatch")
    pkg = StrategyPackage(
        manifest=PackageManifest.model_validate(manifest),
        strategy_spec=validate_spec_v2(raw["strategy_spec"]),
        strategy_contract=validate_contract(raw["strategy_contract"]),
        invariants=validate_invariants(raw["invariants"]),
        parameters=dict(raw.get("parameters") or {}),
        data_requirements=dict(raw.get("data_requirements") or {}),
        lineage=LineageRecord.model_validate(lineage_raw) if lineage_raw else None,
        escape_hatch=validate_escape_hatch(escape_raw) if escape_raw else None,
        readme=str(raw.get("readme") or ""),
    )
    actual = pkg.compute_hash()
    if actual != expected:
        raise SpecV2Error(f"corrupted package / hash mismatch: expected={expected} actual={actual}")
    return pkg


def package_contains_secrets(pkg: StrategyPackage | dict[str, Any]) -> int:
    data = pkg.to_export_dict() if isinstance(pkg, StrategyPackage) else pkg
    return len(find_secrets(data))

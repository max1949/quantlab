"""QLN-2 Strategy Spec v2 / Contract / Package — public API."""

from __future__ import annotations

from engine.strategies.v2.compiler import (
    GENERATOR_VERSION_V2,
    compile_spec_v2,
    compile_spec_v2_deterministic,
)
from engine.strategies.v2.contract import StrategyContract, validate_contract
from engine.strategies.v2.escape_hatch import (
    CodeEscapeHatch,
    CustomComponentDecl,
    validate_escape_hatch,
)
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.invariants import (
    InvariantRule,
    StrategyInvariants,
    validate_invariants,
)
from engine.strategies.v2.lineage import LineageRecord, derive_child_lineage
from engine.strategies.v2.migrate import migrate_v1_to_v2, migrate_v1_file_to_v2
from engine.strategies.v2.package import (
    StrategyPackage,
    export_package,
    import_package,
    package_contains_secrets,
)
from engine.strategies.v2.semantic_diff import SemanticDiffResult, semantic_diff
from engine.strategies.v2.spec_v2 import StrategySpecV2, validate_spec_v2

__all__ = [
    "CodeEscapeHatch",
    "CustomComponentDecl",
    "GENERATOR_VERSION_V2",
    "InvariantRule",
    "LineageRecord",
    "SemanticDiffResult",
    "SpecV2Error",
    "StrategyContract",
    "StrategyInvariants",
    "StrategyPackage",
    "StrategySpecV2",
    "compile_spec_v2",
    "compile_spec_v2_deterministic",
    "derive_child_lineage",
    "export_package",
    "import_package",
    "migrate_v1_file_to_v2",
    "migrate_v1_to_v2",
    "package_contains_secrets",
    "semantic_diff",
    "validate_contract",
    "validate_escape_hatch",
    "validate_invariants",
    "validate_spec_v2",
]

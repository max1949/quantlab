"""Data Trust Gate — mandatory before evidence-producing experiments (QLN-3).

Wraps and strengthens engine.data.data_gate; fail closed for Trust Gate FAIL.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from engine.data.data_gate import DataProvenance, DataGateResult, run_data_gate
from engine.domain.hashing import HashKind, compute_hash
from engine.experiment.errors import ExperimentError
from engine.experiment.time_governance import (
    TimeGovernance,
    assert_frame_time_governance,
    validate_time_governance,
)


@dataclass
class DataTrustGateResult:
    status: str  # PASS | FAIL
    data_gate: dict[str, Any]
    dataset_hash: str | None
    dataset_version: str
    time_governance: dict[str, Any]
    provenance: dict[str, Any]
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def _index_info(df: pd.DataFrame) -> dict[str, Any]:
    if not isinstance(df.index, pd.DatetimeIndex):
        return {"tz_aware": False, "monotonic": False, "duplicates": 0}
    return {
        "tz_aware": df.index.tz is not None,
        "monotonic": bool(df.index.is_monotonic_increasing),
        "duplicates": int(df.index.duplicated().sum()),
    }


def run_data_trust_gate(
    df: pd.DataFrame,
    *,
    provenance: DataProvenance | dict[str, Any] | None = None,
    time_governance: TimeGovernance | dict[str, Any] | None = None,
    dataset_version: str = "v1",
    timeframe: str | None = None,
    require_broker_specific: bool = False,
) -> DataTrustGateResult:
    """Mandatory Data Trust Gate. WARN from lower gate upgrades to FAIL for evidence runs."""
    tg = validate_time_governance(time_governance or TimeGovernance())
    gate: DataGateResult = run_data_gate(
        df,
        provenance=provenance,
        timeframe=timeframe,
        require_broker_specific=require_broker_specific,
    )
    issues = list(gate.issues_tech) + list(gate.issues_zh)
    try:
        assert_frame_time_governance(_index_info(df), tg)
    except ExperimentError as exc:
        issues.append(str(exc))

    # Evidence-producing experiments: WARN is not acceptable — fail closed.
    if gate.status != "PASS":
        issues.append(f"data_gate_status={gate.status}")

    dataset_hash = gate.provenance.get("normalized_hash")
    if not dataset_hash and len(df) > 0:
        # Fallback hash of canonical payload
        cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
        payload = {
            "index": [str(x) for x in df.index.tolist()],
            "columns": {c: df[c].astype(float).tolist() for c in cols},
        }
        dataset_hash = compute_hash(HashKind.DATASET, payload)

    status = "PASS" if not issues and gate.status == "PASS" else "FAIL"
    return DataTrustGateResult(
        status=status,
        data_gate=gate.to_dict(),
        dataset_hash=dataset_hash,
        dataset_version=dataset_version,
        time_governance=tg.canonical_dict(),
        provenance=dict(gate.provenance),
        issues=issues,
    )


def require_data_trust_pass(result: DataTrustGateResult) -> DataTrustGateResult:
    if not result.passed:
        raise ExperimentError(
            "DATA_TRUST_GATE=FAIL: " + "; ".join(result.issues[:8] or ["unknown"])
        )
    return result

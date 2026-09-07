"""Immutable ExperimentRecord — canonical research asset (QLN-3)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from engine.domain.hashing import HashKind, compute_hash, fingerprint_engine
from engine.domain.ids import DomainEntityKind, new_domain_id
from engine.experiment.assumptions import CostAttribution, ExecutionAssumptions
from engine.experiment.errors import ExperimentError
from engine.experiment.time_governance import TimeGovernance
from engine.experiment.tolerances import TOLERANCE_VERSION


class ExperimentRecord(BaseModel):
    """Immutable once sealed. Mutations create a new experiment_id (append-only ledger)."""

    schema_version: Literal["1.0"] = "1.0"
    experiment_id: str
    created_at: str
    strategy_id: str
    strategy_version: str
    strategy_definition_hash: str
    dataset_id: str
    dataset_version: str
    dataset_hash: str
    time_governance: TimeGovernance
    execution_assumptions: ExecutionAssumptions
    engine_name: str
    engine_version: str
    adapter_version: str
    engine_fingerprint: str
    random_seed: int
    cost_attribution: CostAttribution = Field(default_factory=CostAttribution)
    config: dict[str, Any] = Field(default_factory=dict)
    config_hash: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifact_hashes: dict[str, str] = Field(default_factory=dict)
    data_trust_status: str = "PASS"
    data_trust: dict[str, Any] = Field(default_factory=dict)
    evidence_stage: str = "E1_BACKTEST"
    parent_experiment_id: str | None = None
    notes: str = ""
    sealed: bool = True
    content_hash: str = ""
    tolerance_version: str = TOLERANCE_VERSION

    @model_validator(mode="after")
    def _fill_hashes(self) -> ExperimentRecord:
        if not self.config_hash:
            object.__setattr__(
                self,
                "config_hash",
                compute_hash(HashKind.CONFIG, self.config),
            )
        if not self.content_hash:
            object.__setattr__(self, "content_hash", self.compute_content_hash())
        return self

    def compute_content_hash(self) -> str:
        payload = self.model_dump(mode="json")
        # content_hash must not include itself
        payload.pop("content_hash", None)
        # created_at is wall clock — exclude from semantic content hash
        payload.pop("created_at", None)
        return compute_hash(HashKind.ARTIFACT, payload)

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def build_experiment_record(
    *,
    strategy_id: str,
    strategy_version: str,
    strategy_definition_hash: str,
    dataset_id: str,
    dataset_version: str,
    dataset_hash: str,
    time_governance: TimeGovernance | dict[str, Any],
    execution_assumptions: ExecutionAssumptions | dict[str, Any],
    engine_name: str,
    engine_version: str,
    adapter_version: str,
    random_seed: int,
    config: dict[str, Any],
    metrics: dict[str, Any],
    artifact_hashes: dict[str, str],
    data_trust_status: str,
    data_trust: dict[str, Any],
    cost_attribution: CostAttribution | dict[str, Any] | None = None,
    evidence_stage: str = "E1_BACKTEST",
    parent_experiment_id: str | None = None,
    notes: str = "",
    experiment_id: str | None = None,
) -> ExperimentRecord:
    if data_trust_status != "PASS":
        raise ExperimentError("cannot seal experiment when DATA_TRUST_GATE != PASS")
    if not dataset_hash.strip():
        raise ExperimentError("dataset_hash required")
    if not strategy_definition_hash.strip():
        raise ExperimentError("strategy_definition_hash required")

    tg = (
        time_governance
        if isinstance(time_governance, TimeGovernance)
        else TimeGovernance.model_validate(time_governance)
    )
    ea = (
        execution_assumptions
        if isinstance(execution_assumptions, ExecutionAssumptions)
        else ExecutionAssumptions.model_validate(execution_assumptions)
    )
    ca = CostAttribution()
    if isinstance(cost_attribution, CostAttribution):
        ca = cost_attribution
    elif isinstance(cost_attribution, dict):
        ca = CostAttribution.model_validate(cost_attribution)

    eng_fp = fingerprint_engine(
        engine_name=engine_name,
        engine_version=engine_version,
        adapter_version=adapter_version,
    )
    eid = experiment_id or new_domain_id(DomainEntityKind.EXPERIMENT).value
    return ExperimentRecord(
        experiment_id=eid,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        strategy_definition_hash=strategy_definition_hash,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        time_governance=tg,
        execution_assumptions=ea,
        engine_name=engine_name,
        engine_version=engine_version,
        adapter_version=adapter_version,
        engine_fingerprint=eng_fp,
        random_seed=int(random_seed),
        cost_attribution=ca,
        config=dict(config),
        metrics=dict(metrics),
        artifact_hashes=dict(artifact_hashes),
        data_trust_status=data_trust_status,
        data_trust=dict(data_trust),
        evidence_stage=evidence_stage,
        parent_experiment_id=parent_experiment_id,
        notes=notes,
        sealed=True,
    )

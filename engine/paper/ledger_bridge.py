"""Bridge Paper evaluation → QLN-3 Experiment Ledger (append-only)."""

from __future__ import annotations

from typing import Any

from engine.domain.hashing import HashKind, compute_hash
from engine.experiment.assumptions import CostAttribution, ExecutionAssumptions
from engine.experiment.ledger import ExperimentLedger
from engine.experiment.record import ExperimentRecord, build_experiment_record
from engine.experiment.time_governance import TimeGovernance
from engine.paper.evaluation import PaperEvaluation


def paper_evaluation_to_experiment(
    evaluation: PaperEvaluation,
    *,
    dataset_hash: str,
    dataset_id: str = "paper_run_dataset",
    dataset_version: str = "v1",
    random_seed: int = 0,
    engine_version: str = "paper_runner",
    adapter_version: str = "paper_ledger_bridge_v1",
    execution_assumptions: ExecutionAssumptions | None = None,
) -> ExperimentRecord:
    """Seal a Paper evaluation as an ExperimentRecord (Data Trust already assumed upstream)."""
    if evaluation.evaluation_status not in {"COMPLETE", "FAILED", "INSUFFICIENT_EVIDENCE"}:
        # RUNNING must not seal
        from engine.experiment.errors import ExperimentError

        raise ExperimentError("cannot seal running paper evaluation into experiment ledger")

    strat_hash = compute_hash(
        HashKind.STRATEGY_DEFINITION,
        {
            "strategy_id": evaluation.strategy_spec_id,
            "version": evaluation.strategy_spec_version,
        },
    )
    metrics = {
        **dict(evaluation.performance_summary),
        "parity_status": evaluation.parity_status,
        "evaluation_status": evaluation.evaluation_status,
    }
    artifact_hashes = {
        "evaluation": compute_hash(HashKind.ARTIFACT, evaluation.to_dict()),
        "dataset": dataset_hash,
    }
    return build_experiment_record(
        strategy_id=evaluation.strategy_spec_id,
        strategy_version=evaluation.strategy_spec_version,
        strategy_definition_hash=strat_hash,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        time_governance=TimeGovernance(),
        execution_assumptions=execution_assumptions or ExecutionAssumptions(
            fee_model="paper_sandbox",
            slippage_model="paper_sandbox",
            notes=f"paper_run_id={evaluation.paper_run_id}",
        ),
        engine_name="quantlab_paper",
        engine_version=engine_version,
        adapter_version=adapter_version,
        random_seed=random_seed,
        config={
            "paper_run_id": evaluation.paper_run_id,
            "backtest_run_id": evaluation.backtest_run_id,
            "parity_status": evaluation.parity_status,
        },
        metrics=metrics,
        artifact_hashes=artifact_hashes,
        data_trust_status="PASS",
        data_trust={"source": "paper_evaluation_bridge", "note": "caller must enforce trust upstream"},
        cost_attribution=CostAttribution(notes="paper sandbox evaluation"),
        evidence_stage="E4_PAPER",
        notes="; ".join(evaluation.research_feedback_zh[:3]),
    )


def append_paper_evaluation_to_ledger(
    evaluation: PaperEvaluation,
    *,
    ledger: ExperimentLedger,
    dataset_hash: str,
    **kwargs: Any,
) -> ExperimentRecord:
    rec = paper_evaluation_to_experiment(evaluation, dataset_hash=dataset_hash, **kwargs)
    return ledger.append(rec)

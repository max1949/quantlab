"""One-click reproduce — compare sealed experiment vs fresh rerun."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from engine.experiment.errors import ReproduceError
from engine.experiment.ledger import ExperimentLedger
from engine.experiment.record import ExperimentRecord
from engine.experiment.runner import run_golden_ema_experiment
from engine.experiment.tolerances import GOLDEN_REPRODUCE_TOLERANCES


@dataclass
class ReproduceReport:
    experiment_id: str
    status: str  # PASS | FAIL
    tolerance_version: str
    deltas: dict[str, float] = field(default_factory=dict)
    mismatches: list[str] = field(default_factory=list)
    original_metrics: dict[str, Any] = field(default_factory=dict)
    reproduced_metrics: dict[str, Any] = field(default_factory=dict)
    reproduced_experiment_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def _abs_delta(a: Any, b: Any) -> float:
    return abs(float(a) - float(b))


def compare_records(
    original: ExperimentRecord,
    reproduced: ExperimentRecord,
    *,
    tolerances: dict[str, Any] | None = None,
) -> ReproduceReport:
    tol = dict(tolerances or GOLDEN_REPRODUCE_TOLERANCES)
    mismatches: list[str] = []
    deltas: dict[str, float] = {}

    if tol.get("require_identical_seed") and original.random_seed != reproduced.random_seed:
        mismatches.append("random_seed")
    if tol.get("require_identical_dataset_hash") and original.dataset_hash != reproduced.dataset_hash:
        mismatches.append("dataset_hash")
    if tol.get("require_identical_config_hash") and original.config_hash != reproduced.config_hash:
        mismatches.append("config_hash")
    if (
        tol.get("require_identical_strategy_hash")
        and original.strategy_definition_hash != reproduced.strategy_definition_hash
    ):
        mismatches.append("strategy_definition_hash")

    metric_keys = {
        "total_return": "total_return_abs",
        "max_drawdown": "max_drawdown_abs",
        "final_equity": "final_equity_abs",
        "sharpe": "sharpe_abs",
    }
    for key, tol_key in metric_keys.items():
        if key not in original.metrics or key not in reproduced.metrics:
            mismatches.append(f"missing_metric:{key}")
            continue
        d = _abs_delta(original.metrics[key], reproduced.metrics[key])
        deltas[key] = d
        if d > float(tol[tol_key]):
            mismatches.append(f"metric_drift:{key}={d}>{tol[tol_key]}")

    # trade_count exact
    ot = int(original.metrics.get("trade_count", -1))
    rt = int(reproduced.metrics.get("trade_count", -2))
    deltas["trade_count"] = float(abs(ot - rt))
    if abs(ot - rt) > int(tol.get("trade_count_abs", 0)):
        mismatches.append(f"metric_drift:trade_count")

    status = "PASS" if not mismatches else "FAIL"
    return ReproduceReport(
        experiment_id=original.experiment_id,
        status=status,
        tolerance_version=str(tol.get("tolerance_version")),
        deltas=deltas,
        mismatches=mismatches,
        original_metrics=dict(original.metrics),
        reproduced_metrics=dict(reproduced.metrics),
        reproduced_experiment_id=reproduced.experiment_id,
    )


def reproduce_experiment(
    original: ExperimentRecord | str,
    *,
    ledger: ExperimentLedger | None = None,
    append_reproduction: bool = False,
) -> ReproduceReport:
    """One-click reproduce for golden EMA experiments.

    Loads by id from ledger when a string is given.
    """
    if isinstance(original, str):
        if ledger is None:
            raise ReproduceError("ledger required to load experiment by id")
        rec = ledger.get(original)
        if rec is None:
            raise ReproduceError(f"experiment not found: {original}")
        original = rec

    if original.strategy_id != "golden_01_ema_trend":
        raise ReproduceError(
            f"QLN-3 one-click reproduce currently supports golden_01_ema_trend; "
            f"got {original.strategy_id}"
        )

    cfg = original.config
    reproduced = run_golden_ema_experiment(
        seed=int(cfg.get("seed", original.random_seed)),
        n_bars=int(cfg.get("n_bars", 400)),
        fast=int(cfg.get("fast_ema", 10)),
        slow=int(cfg.get("slow_ema", 20)),
        fee_rate=float(original.execution_assumptions.fee_rate),
        slippage_bps=float(original.execution_assumptions.slippage_bps),
    )
    # Link lineage without mutating original
    reproduced = reproduced.model_copy(
        update={
            "parent_experiment_id": original.experiment_id,
            "notes": f"reproduction of {original.experiment_id}",
            "content_hash": "",  # recompute
        }
    )
    # Force content hash refresh
    object.__setattr__(reproduced, "content_hash", reproduced.compute_content_hash())

    report = compare_records(original, reproduced)
    if append_reproduction and ledger is not None and report.passed:
        ledger.append(reproduced)
    if not report.passed:
        raise ReproduceError(
            f"REPRODUCE=FAIL mismatches={report.mismatches} deltas={report.deltas}"
        )
    return report

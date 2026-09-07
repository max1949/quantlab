"""Pre-declared numerical tolerances for Golden Experiment reproduce (QLN-3).

MUST NOT be changed post-hoc to excuse drift. Amend only via Owner-approved
governance change with a new tolerance version id.
"""

from __future__ import annotations

from typing import Any

# Tolerance schema version — bump only with explicit Owner/governance amendment.
TOLERANCE_VERSION = "qln3_golden_tol_v1"

GOLDEN_REPRODUCE_TOLERANCES: dict[str, Any] = {
    "tolerance_version": TOLERANCE_VERSION,
    # Absolute tolerances on summary metrics (pre-declared).
    "total_return_abs": 1e-12,
    "max_drawdown_abs": 1e-12,
    "trade_count_abs": 0,  # exact
    "final_equity_abs": 1e-9,
    "sharpe_abs": 1e-9,
    # Dataset / artifact identity must match exactly.
    "require_identical_dataset_hash": True,
    "require_identical_config_hash": True,
    "require_identical_strategy_hash": True,
    "require_identical_seed": True,
}

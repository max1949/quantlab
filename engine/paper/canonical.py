"""QLN-5 Paper path disposition — REPAIR / MERGE / RETIRE (no rewrite)."""

from __future__ import annotations

from enum import Enum
from typing import Any


class PaperPathDisposition(str, Enum):
    CANONICAL = "CANONICAL"
    SOFT_RETIRE = "SOFT_RETIRE"
    HARDEN = "HARDEN"
    ADJACENT_RESEARCH = "ADJACENT_RESEARCH"


# Authoritative map for product + ops. History tables are never deleted here.
PAPER_PATH_REGISTRY: dict[str, dict[str, Any]] = {
    "paper_run": {
        "disposition": PaperPathDisposition.CANONICAL.value,
        "paths": [
            "backend/app/services/paper_run_service.py",
            "scripts/paper_runner.py",
            "engine/nautilus/paper_node.py",
            "frontend-react/src/pages/PaperTrading.tsx",
        ],
        "api": "/paper-sandbox/*",
        "notes": "Official Spec→runtime_params→PaperRun path",
    },
    "runtime_params": {
        "disposition": PaperPathDisposition.CANONICAL.value,
        "paths": ["engine/strategies/runtime_params.py"],
        "notes": "SSOT for Backtest+Paper params",
    },
    "paper_orders": {
        "disposition": PaperPathDisposition.SOFT_RETIRE.value,
        "paths": [
            "backend/app/services/execution_service.py",
            "frontend-react/src/components/PaperExecutionPanel.tsx",
        ],
        "api": "/execution/paper/*",
        "notes": "Legacy mastery paper orders — hide from primary UX; keep history",
    },
    "sandbox_runtime": {
        "disposition": PaperPathDisposition.SOFT_RETIRE.value,
        "paths": ["engine/paper/sandbox_runtime.py", "engine/paper/signal_engine.py"],
        "notes": "Non-canonical scaffold; not Evidence authority",
    },
    "kill_switch": {
        "disposition": PaperPathDisposition.HARDEN.value,
        "paths": ["engine/paper/kill_switch.py"],
        "notes": "PaperRun fields are authority for official path",
    },
    "restart_recovery": {
        "disposition": PaperPathDisposition.HARDEN.value,
        "paths": ["engine/paper/recovery.py"],
        "notes": "Block duplicate entry after crash",
    },
    "paper_evaluation": {
        "disposition": PaperPathDisposition.HARDEN.value,
        "paths": ["engine/paper/evaluation.py", "engine/paper/ledger_bridge.py"],
        "notes": "Bind evaluation → Experiment Ledger",
    },
}


def canonical_paper_apis() -> list[str]:
    return ["/paper-sandbox/*"]


def soft_retired_paper_apis() -> list[str]:
    return ["/execution/paper/*"]


def assert_no_real_money_in_registry() -> None:
    for meta in PAPER_PATH_REGISTRY.values():
        blob = str(meta).lower()
        assert "live_route" not in blob or "deny" in blob

"""Phase 6 paper sandbox domain (no FastAPI imports)."""

from engine.paper.gates import RealtimeDataGateResult, run_realtime_data_gate
from engine.paper.kill_switch import KillSwitchScope, check_kill_switch
from engine.paper.manifest import RunManifest, build_run_manifest
from engine.paper.paper_entry_gate import PaperEntryGateResult, run_paper_entry_gate
from engine.paper.risk_policy import PaperRiskPolicy, RiskEvent, evaluate_risk

__all__ = [
    "KillSwitchScope",
    "PaperEntryGateResult",
    "PaperRiskPolicy",
    "RealtimeDataGateResult",
    "RiskEvent",
    "RunManifest",
    "build_run_manifest",
    "check_kill_switch",
    "evaluate_risk",
    "run_paper_entry_gate",
    "run_realtime_data_gate",
]

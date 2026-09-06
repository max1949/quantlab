# QUANTLAB_QLN0_CONSTITUTION_GAP_LEDGER

```text
PHASE=QLN-0
MODE=READ_ONLY
MAPS_TO=QLN-1..QLN-12
DO_NOT_STUFF_ALL_INTO_QLN-1=YES
```

| Constitutional requirement | Current capability | Evidence | Gap | Target QLN | Priority | Dependency |
|---|---|---|---|---|---|---|
| Domain single vocabulary | Partial ad hoc statuses | models + lifecycle.py + validation decision | Duplicate lifecycle vocab across Factor/Spec/Paper | QLN-1 | P0 | none |
| Engine Interface abstraction | Adapter modules exist | `engine/nautilus/*` | Not formal Engine Interface contracts | QLN-1 | P0 | domain IDs |
| Strategy Spec v2 | Spec v1 only | `engine/strategies/spec.py` | Missing Contract/Package/Invariants depth | QLN-2 | P0 | QLN-1 |
| Strategy Package portable | Examples on disk | `strategy_specs/examples/` | No signed/hash-export package format | QLN-2 | P1 | Spec v2 |
| Experiment Ledger immutable | NO | No ExperimentRecord model/name match | Missing ledger | QLN-3 | P0-B | QLN-1 hashes |
| One-click reproduce | PARTIAL | snapshots + golden scripts | Not universal Experiment reproduce | QLN-3 | P0 | ledger |
| Data Trust Gate (full) | PARTIAL | `engine/data/data_gate.py` | Not mandatory evidence gate everywhere | QLN-3 | P0 | — |
| Time Governance UTC policy | PARTIAL | Spec timezone fields | Not enforced as governance layer | QLN-3 | P1 | — |
| Evidence Pipeline Promote/Hold/Kill | PARTIAL | `engine/validation/decision.py` REJECT/HOLD/PROMOTE | Not productized Pre-Capital Review UX; Paper often INSUFFICIENT | QLN-4 | P0-A | QLN-3 |
| Reality Score | NO | — | Absent | QLN-4 | P0 | Evidence core |
| Research Debt display | NO | — | Absent | QLN-4 | P1 | — |
| OOS / WF / stress | PARTIAL / YES | walk_forward + validation pipeline + batch_001 | Not all wired as blocking product Gate for all strategies | QLN-4 | P0 | — |
| Paper Sandbox canonical closure | PARTIAL | PaperRun exists; dual paper remains | Fragmentation F2 | QLN-5 | P0-C | QLN-1 mapping |
| Strategy DNA / Genealogy | PARTIAL | Spec parent_version; no full DNA | Weak | QLN-6 | P1 | Spec v2 |
| Strategy Graveyard durable | PARTIAL | JSONL graveyard | Not Research Memory DB | QLN-6 | P1 | — |
| Bounded AI Scientist / Skeptic | PARTIAL | builder + validation reject | Generator still prominent in nav | QLN-6 | P1 | doctrine |
| Portfolio Governor | NO / PARTIAL | basic portfolio helpers | No crowding governor | QLN-7 | P2 | multi-strategy evidence |
| Shadow Twin / Flight Recorder | NO | — | Absent | QLN-8 | P0-C later | Paper stable |
| Chaos / Secret Plane / RBAC harden | PARTIAL | flags, kill switch, JWT | Not Chaos Lab | QLN-9 | P1 | — |
| Broker Capability Matrix | NO | retired channels only | Absent | QLN-9 | P1 | — |
| Canary Live readiness | NO | LIVE DENY | Correctly absent | QLN-10 | — | Owner |
| Limited Live Pilot | NO | — | Correctly absent | QLN-11 | — | Owner |
| Evidence Passport / TMOS link / commercial | NO | — | Correctly absent | QLN-12 | — | evidence mature |
| Amendment Proof Before Capital wedge | PARTIAL | validation batch rejects | Product wedge UX missing | QLN-4/UX | P0 | Evidence pipeline |

## Experiment / Evidence maturity snapshot

| Capability | Maturity |
|---|---|
| Experiment Ledger | NO |
| reproducibility | PARTIAL |
| code hash | PARTIAL (compiled_hash / content_hash) |
| config hash | PARTIAL |
| dataset version | PARTIAL (snapshots) |
| engine version | PARTIAL (`config/nautilus-version.yaml`) |
| fee/slippage model logging | PARTIAL |
| random seed | PARTIAL / NO systematic |
| Data Trust | PARTIAL |
| Reality Score | NO |
| Strategy Genealogy | PARTIAL |
| Strategy Graveyard | PARTIAL |
| Evidence Pipeline | PARTIAL |
| Promotion / Hold / Kill | PARTIAL (engine decision; limited product surface) |
| Strategy Passport | NO |
| Research Memory | PARTIAL (projects/graph/reports) |

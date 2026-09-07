# QLN-3 Work Ledger

```text
PHASE=QLN-3
TITLE=Experiment Ledger / Data Trust / Reproducibility Core
CAMPAIGN=QUANTLAB_QLN_3_TO_10_AUTONOMOUS_CAMPAIGN
OWNER_PREAUTHORIZATION=YES
QLN_3_ENTRY_GATE=PASS
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
PERSISTENT_DB_SCHEMA_CHANGE=DENY
EXPERIMENT_LEDGER_BUILD=YES
EVIDENCE_PIPELINE_BUILD=NO
PAPER_EXPANSION=NO
LIVE_BUILD=NO
REAL_MONEY=NO
QLN_11_AUTO_ENTER=DENY
```

## Scope executed

| Workstream | Path | Status |
|---|---|---|
| ExperimentRecord (immutable) | `engine/experiment/record.py` | DONE |
| Append-only ledger (JSONL) | `engine/experiment/ledger.py` | DONE |
| Time governance | `engine/experiment/time_governance.py` | DONE |
| Execution assumptions + cost attribution | `engine/experiment/assumptions.py` | DONE |
| Data Trust Gate (mandatory, fail-closed) | `engine/experiment/data_trust.py` | DONE |
| Golden EMA domain runner | `engine/experiment/runner.py` | DONE |
| One-click reproduce + pre-declared tolerances | `engine/experiment/reproduce.py`, `tolerances.py` | DONE |
| Tests | `engine/tests/test_experiment_ledger_qln3.py` | DONE |
| Campaign ledger | `docs/governance/campaigns/…` | DONE |

## Non-goals preserved

- QLN-4 Evidence Validation Pipeline (Promotion/Kill full matrix) — next phase
- Paper/Shadow/Live / DB Alembic / UI

```text
QLN_3_STRUCTURAL_DB_CHANGE_REQUIRED=NO
```

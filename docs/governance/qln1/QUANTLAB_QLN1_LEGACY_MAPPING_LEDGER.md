# QUANTLAB_QLN1_LEGACY_MAPPING_LEDGER

```text
PHASE=QLN-1
SOURCE=engine/domain/legacy_mapping.py + QLN-0 Capability Asset Ledger
DESTRUCTIVE_RETIREMENT=DENY
```

Code SSOT: `engine/domain/legacy_mapping.py`

## Strategy lifecycle

| Legacy | Canonical | Disposition |
|---|---|---|
| DRAFT | DRAFT | MIGRATE |
| BACKTESTED | RESEARCH_ACTIVE | MIGRATE |
| VALIDATED | CANDIDATE | MIGRATE |
| ROBUST | CANDIDATE | MIGRATE |
| PAPER_READY | PAPER_APPROVED | MIGRATE |

## Environment

| Legacy | Canonical | Disposition |
|---|---|---|
| SANDBOX | PAPER | MERGE (alias) |
| PAPER / BACKTEST / SHADOW / LIVE | same | KEEP/HARDEN |
| SIM | BACKTEST | MERGE |

## Execution channels

| Legacy | Canonical ExecutionMode | Disposition |
|---|---|---|
| paper (paper_orders) | PAPER | SOFT_RETIRE |
| nautilus_paper / PaperRun | PAPER | KEEP |
| vectorized_sim | SIMULATION | KEEP |
| vnpy | NO_EXECUTION | ARCHIVE |
| qmt | NO_EXECUTION | SOFT_RETIRE |

## PaperRunStatus

Kept as Run-domain states (`RUN.CREATED`…`RUN.KILLED`) — **not** merged into StrategyLifecycle.

## Assets (from QLN-0)

| Asset | Disposition | QLN target if action |
|---|---|---|
| Factor Lab vectorized BT | KEEP | — |
| Nautilus BT / PaperRun | KEEP | QLN-5 harden |
| paper_orders / sandbox_runtime | SOFT_RETIRE | QLN-5 |
| execution_adapter / QMT | SOFT_RETIRE | QLN-9 |
| vn.py | ARCHIVE | — |
| Spec v1 | MIGRATE | QLN-2 |

```text
LEGACY_PATHS_RETIRED=0
LEGACY_PATHS_HELD=paper_orders,sandbox_runtime,execution_adapter,QMT,vn.py,UX_EMA_examples
HISTORICAL_DATA_PRESERVED=YES
```

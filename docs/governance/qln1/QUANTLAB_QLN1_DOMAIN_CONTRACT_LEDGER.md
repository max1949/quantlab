# QUANTLAB_QLN1_DOMAIN_CONTRACT_LEDGER

```text
PHASE=QLN-1
SSOT_PACKAGE=engine/domain
DB_PERSISTENCE=NOT_IN_SCOPE
```

| Contract | Module | Notes |
|---|---|---|
| Domain IDs | `ids.py` | `ql_<prefix>_<32hex>`; PK ≠ DomainId |
| StrategyLifecycle | `enums.py` | Separate from Environment / Evidence |
| EvidenceStage | `enums.py` | E0…E7 + UNKNOWN; no skip-ahead |
| Environment | `environment.py` | TEST/DEV/BACKTEST/PAPER/SHADOW/CANARY/LIVE |
| ExecutionMode | `enums.py` | NO_EXECUTION/READ_ONLY/SIMULATION/PAPER/SHADOW/LIVE |
| Version semantics | `versioning.py` | ChangeClass A–D → VersionBump |
| Hash policy | `hashing.py` | deterministic; strips secrets + timestamps |
| AuditEvent | `audit.py` | actor/action/target/states/env/correlation |
| Engine interfaces | `engine_contracts.py` | Backtest + Paper ports; shared field semantics |
| Defaults | `defaults.py` | EMA 10/20 canonical; EXAMPLE≠DEFAULT |

## Concept isolation rules

1. `StrategyLifecycle` must not encode BACKTEST/PAPER/LIVE as lifecycle identity.
2. `EvidenceStage` records evidence progress; absence of capability ≠ stage deletion.
3. `Environment` is where code runs; `ExecutionMode` is how it may act.
4. PaperRunStatus remains a **Run** state machine (legacy), mapped as `RUN.*`.

# QLN-3 Similar-Issue Audit

```text
SIMILAR_ISSUE_AUDIT=REQUIRED
SIMILAR_ISSUE_AUDIT=PASS
```

## In-phase findings

| Pattern | Finding | Resolution |
|---|---|---|
| Data Gate vs Data Trust | Precursor `run_data_gate` WARN allowed; Trust Gate for evidence must fail closed | `run_data_trust_gate` upgrades non-PASS → FAIL; seal requires PASS |
| Paper RunManifest vs ExperimentRecord | Overlapping reproducibility fields | Distinct: Paper runtime manifest vs research Experiment Ledger; QLN-5 will bind Paper→Ledger |
| Hash policy duplication | Multiple hash helpers | Experiment uses QLN-1 `engine.domain.hashing` only |
| Nautilus vs domain golden runner | Dual backtest engines | QLN-3 Golden Acceptance uses **domain EMA runner** (Nautilus-independent); Nautilus golden remains adapter regression — documented, not semantic conflict for Ledger |
| Mutable ledger risk | In-place update temptation | Append-only JSONL; duplicate id → error |

## Out-of-phase HOLD

| Item | Target |
|---|---|
| Wire all Celery/API backtests to Experiment Ledger | QLN-4/5 product cutover |
| Paper evaluation → Ledger | QLN-5 |
| Full Promotion/Kill evidence pipeline | QLN-4 |
| Persistent DB experiment table | Only if Owner approves structural DB — currently DENY / filesystem SSOT |

## Residual

Filesystem ledger is SSOT for QLN-3 Acceptance. Concurrent multi-writer locking is not required for single-node research MVP; document for QLN-9 ops hardening.

# QLN-5 Acceptance Ledger

```text
PHASE=QLN-5
QLN_5=PASS
PAPER_SANDBOX_CANONICAL_CLOSURE=PASS
REPAIR_MERGE_RETIRE_NOT_REWRITE=YES
CANONICAL_PAPERRUN_PATH=PASS
SOFT_RETIRE_PAPER_ORDERS_UX=PASS
SOFT_RETIRE_SANDBOX_RUNTIME=PASS
BACKTEST_PAPER_PARAM_SEMANTIC_PARITY=PASS
KILL_SWITCH_CONTRACT=PASS
RESTART_RECOVERY_CONTRACT=PASS
PAPER_EVAL_TO_EXPERIMENT_LEDGER=PASS
CHINESE_PAPER_UX_OFFICIAL=PASS
REAL_MONEY_PATH=0
LIVE_ROUTE=DENY
SIMILAR_ISSUE_AUDIT=PASS
UNAUTHORIZED_SCOPE_EXPANSION=NO
QLN_6_STARTED=NO
```

## Notes

- Param-level Spec→Paper SSOT parity proven (EMA/size/instrument). Full tick fill parity remains owned by existing Phase-6 PaperRun/`paper_node` path (not rewritten).
- Legacy `/execution/paper/*` retained for history; marked SOFT_RETIRE with Chinese UX notice.
- QLN-6 Entry requires multiple higher-Evidence strategies with real research demand — do not forge.

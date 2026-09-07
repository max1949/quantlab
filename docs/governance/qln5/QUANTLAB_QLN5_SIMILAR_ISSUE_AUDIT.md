# QLN-5 Similar-Issue Audit

```text
SIMILAR_ISSUE_AUDIT=PASS
```

| Pattern | Resolution |
|---|---|
| Dual Paper APIs | Registry marks `/paper-sandbox/*` CANONICAL; `/execution/paper/*` SOFT_RETIRE |
| Dual runtimes | sandbox_runtime SOFT_RETIRE constant + docstring; paper_node KEEP |
| Evaluation unbound from Ledger | `ledger_bridge` + wire in `paper_run_service._finalize_run_evaluation` |
| Kill authority split | PaperRun kill fields remain official; contract tests on `check_kill_switch` |

HOLD (not blocker): hide L4 legacy panel entirely from nav — optional UX polish post-QLN-5.

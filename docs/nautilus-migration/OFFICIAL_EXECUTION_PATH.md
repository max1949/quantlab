# Official Execution Path (Phase 6 Closure)

```text
OFFICIAL_FUTURE_EXECUTION_ENGINE=NAUTILUSTRADER

Strategy Spec
  → compile_spec (engine/strategies/compiler.py)
  → require_nautilus_runtime_params (SSOT for Backtest + Paper)
  → Nautilus Backtest (engine/nautilus/backtest_adapter.py)
  → Nautilus PaperRun (scripts/paper_runner.py → engine/nautilus/paper_node.py)
  → Shadow (Phase 7 — AUTO_ENTER=DENY)
  → Live (HOLD — Owner gate only)
```

## Legacy compatibility

| Path | Status |
|------|--------|
| `legacy paper_orders` + `execution_adapter` | LEGACY_COMPATIBILITY — mastery/coaching only |
| `vn.py` channel | SOFT_RETIRED — history preserved |
| `QMT` channel | SOFT_RETIRED — NEW_CREATE=DENY |
| `engine/paper/sandbox_runtime.py` | Scaffold — not official runtime |

**NEW_FEATURES=DENY** on legacy execution adapter. All new strategy runtime work goes through PaperRun + Nautilus.

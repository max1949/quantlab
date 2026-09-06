# Official Execution Path (Phase 6 Closure)

> **Numbering note:** “Phase 6 / Phase 7” below are **historical** `QUANTLAB_NAUTILUS_EVOLUTION` route labels. Future construction uses Constitution **QLN-0 → QLN-12** only. See [`docs/governance/QUANTLAB_CONSTITUTION.md`](../governance/QUANTLAB_CONSTITUTION.md).

```text
OFFICIAL_FUTURE_EXECUTION_ENGINE=NAUTILUSTRADER

Strategy Spec
  → compile_spec (engine/strategies/compiler.py)
  → require_nautilus_runtime_params (SSOT for Backtest + Paper)
  → Nautilus Backtest (engine/nautilus/backtest_adapter.py)
  → Nautilus PaperRun (scripts/paper_runner.py → engine/nautilus/paper_node.py)
  → Shadow (historical Phase 7 label — AUTO_ENTER=DENY; maps to future QLN-8+)
  → Live (HOLD — Owner gate only; maps to future QLN-10/11)
```

## Legacy compatibility

| Path | Status |
|------|--------|
| `legacy paper_orders` + `execution_adapter` | LEGACY_COMPATIBILITY — mastery/coaching only |
| `vn.py` channel | SOFT_RETIRED — history preserved |
| `QMT` channel | SOFT_RETIRED — NEW_CREATE=DENY |
| `engine/paper/sandbox_runtime.py` | Scaffold — not official runtime |

**NEW_FEATURES=DENY** on legacy execution adapter. All new strategy runtime work goes through PaperRun + Nautilus.

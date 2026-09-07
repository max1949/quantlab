# QLN-2 Similar-Issue Audit

```text
SIMILAR_ISSUE_AUDIT=REQUIRED
SIMILAR_ISSUE_AUDIT=PASS
```

## Findings in QLN-2 scope (fixed or designed out)

| Pattern | Finding | Resolution |
|---|---|---|
| v1/v2 duplicated semantics | Risk of two SSOT meanings | v1 remains loadable; **v2 is asset SSOT going forward**; migration asserts drift=0; compiler v2 is QLN-2 path |
| duplicate defaults | EMA EXAMPLE≠DEFAULT | Spec v2 requires explicit `fast`/`slow` or `parameters.values`; documents canonical 10/20 without silent UX 20/60 |
| direct Nautilus dependency | Product must not bind to Nautilus classes | `engine/strategies/v2/*` forbids `nautilus_trader` imports (tested) |
| inconsistent hash serialization | Pretty JSON vs hash | Package hash uses `engine.domain.hashing.compute_hash` + canonical bytes; README excluded from hash payload |
| secret leakage | Keys/values in packages | `secrets.py` fail-closed; package export/import assert |
| FE/BE field meaning drift | Out of QLN-2 UI scope | HOLD → UX phase; domain/spec meaning documented in v2 |
| multiple Strategy representations | v1 Spec + v2 Spec + package | Allowed as **format generations** with deterministic migration; package is portable unit |

## Out-of-phase HOLDs (not QLN-2 blockers)

| Item | Target |
|---|---|
| Wire all product paths to Spec v2 exclusively | QLN-3+ / product cutover |
| Full Evidence / Experiment Ledger consuming package hashes | QLN-3 |
| Paper/Shadow runtime consuming escape hatch components | QLN-5/9 |
| UX form generation from Spec v2 | UI phase |

## Residual risk

Legacy `compile_spec` (v1) remains for compatibility; new assets should use `compile_spec_v2`. Dual compiler versions are intentional generation tags (`spec_compiler_v1` / `spec_compiler_v2`), not dual business semantics when migration drift=0.

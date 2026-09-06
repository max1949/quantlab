# QLN-0 Read-Only Reconciliation Report

```text
PHASE=QLN-0
MODE=READ_ONLY
OWNER_AUTHORIZATION=YES
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
QLN_0_MODE=READ_ONLY
AUTO_IMPLEMENT=NO
CODE_CHANGE=NONE
DATABASE_CHANGE=NONE
PRODUCTION_CHANGE=NONE
LIVE_CHANGE=NONE
NEXT_PHASE_AUTO_ENTER=NO
REPO_HEAD=29078ad
DOCUMENTED_PROD_SNAPSHOT=bf935a0 (ancestor; 12 commits behind HEAD as of audit)
AUDIT_DATE=2026-09-07
```

## Governance chain loaded

1. `docs/governance/QUANTLAB_CONSTITUTION.md`
2. Amendment No. 1 Product Value & Commercial Doctrine
3. Autonomous Engineering Pack v1.0 (README + Contract + Change Class Matrix + Acceptance Protocol + Stop Rules)
4. Historical Nautilus Evolution / Phase 0–7 / Paper Sandbox / Strategy Validation docs

```text
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
ALLOWED_CHANGE_CLASSES=Q0,Q1
```

---

## Executive verdict

```text
QLN_0_READ_ONLY_RECONCILIATION=PASS
QLN_1_STARTED=NO
ENGINEERING=FROZEN
STOP=YES
```

QuantLab today is a **dual-stack** system: (A) Factor Lab / Research OS vectorized path, and (B) Nautilus Strategy Spec → PaperRun official execution path. LIVE remains DENY. Historical Phase 6 claims must be re-stated as **workstation-revalidated PARTIAL for production freshness**, not inherited blindly as 20/20.

---

## 1. Current architecture truth

```text
CURRENT_ARCHITECTURE_TRUTH=
  Research OS (Academy/Projects/Factors/Backtests/Validations/Seasons/AI/Reports)
  + Factor vectorized engine (engine/backtest.py, walk_forward, Celery)
  + Nautilus Spec stack (strategy_specs → compiler → runtime_params → backtest_adapter / paper_node)
  + Dual paper surfaces (official PaperRun + legacy paper_orders mastery)
  + Soft-retired QMT/vn.py channels (NEW_CREATE=DENY; residual HTTP code remains)
  + LIVE=DENY (quantlab_live default False; paper_run_service raises LIVE=DENY)
```

Canonical official strategy path (DOCUMENT + CODE):

```text
Strategy Spec
  → compile_spec (engine/strategies/compiler.py)
  → require_nautilus_runtime_params (engine/strategies/runtime_params.py)
  → Nautilus Backtest (engine/nautilus/backtest_adapter.py)
  → PaperRun (backend paper_run_service → scripts/paper_runner.py → engine/nautilus/paper_node.py)
  → Shadow/Live = HOLD (future QLN-8+)
```

Evidence sources used: CODE_TRUTH + TEST_TRUTH + DB_TRUTH (local Alembic) + DOCUMENT_TRUTH. Production deep inspect = **PARTIAL** (public `/health` OK; deploy commit not re-SSH’d this session).

Detailed ledgers:

- [Capability Asset Ledger](./QUANTLAB_QLN0_CAPABILITY_ASSET_LEDGER.md)
- [Architecture Fragmentation Ledger](./QUANTLAB_QLN0_ARCHITECTURE_FRAGMENTATION_LEDGER.md)
- [Constitution Gap Ledger](./QUANTLAB_QLN0_CONSTITUTION_GAP_LEDGER.md)
- [Test Truth Ledger](./QUANTLAB_QLN0_TEST_TRUTH_LEDGER.md)
- [Product Value Alignment Ledger](./QUANTLAB_QLN0_PRODUCT_VALUE_ALIGNMENT_LEDGER.md)

---

## 2. Historical roadmap reconciliation (summary)

| Milestone | Classification | Notes |
|---|---|---|
| Sprint 1–8 Research OS | IMPLEMENTED | Auth, Academy, Factor Lab, Backtest, Validation, Seasons, AI, Reports — code present |
| Sprint 9+ Execution / Growth | PARTIAL / IMPLEMENTED | Billing/orgs/paper/execution routes present; Growth OS coexists |
| Nautilus Phase 0 inventory | HISTORICAL_ONLY | Docs preserved under `docs/nautilus-migration/` |
| Phase 1 golden Nautilus backtest | IMPLEMENTED | `engine/nautilus/backtest_adapter.py` + golden tests |
| Phase 2 Strategy Spec | IMPLEMENTED (v1) | Spec schema/compiler; **not** Spec v2 |
| Phase 3 AI builder | IMPLEMENTED | `engine/ai/strategy_builder.py`; feature-flagged |
| Phase 4 NL→Spec→report | PARTIAL | Pipeline exists; Evidence Ledger incomplete vs Constitution |
| Phase 5 vn.py removal | IMPLEMENTED / SOFT_RETIRE | Channel NEW_CREATE=DENY; residual code kept |
| Phase 5.5 QMT soft retirement | IMPLEMENTED | Same pattern as vn.py |
| Phase 6 Paper Sandbox | PARTIAL / DRIFTED vs claims | Code+local tests strong; do **not** auto-inherit prod 20/20 |
| Phase 7 Shadow/Live | NOT_IMPLEMENTED | Explicit DENY / AUTO_ENTER=NO |
| Strategy Validation mode | PARTIAL | `engine/validation/*`; batch_001 REJECTED=10 PROMOTED=0 |

---

## 3. Top risks

### TOP_ARCHITECTURE_RISKS

1. **Dual stacks** (Factor Lab vs Nautilus Spec) — two metric/result worlds; risk of user/product confusion.
2. **Dual paper runtimes** — official PaperRun vs legacy `paper_orders` still callable from FE.
3. **Latent `_route_gateway` HTTP** in `engine/execution_adapter.py` — soft-retired but not deleted.
4. **Local vs prod flag drift** — local defaults research flags True; historical prod snapshot had many False / later closure enabled some; deploy HEAD not re-verified this session.
5. **No durable Experiment Ledger / Spec DB** — Spec & experiment evidence mostly JSON/files/tables of adjacent domains.

### TOP_SEMANTIC_DRIFTS

1. **UX EMA20/60 examples** (`AiCreateStrategy`, signal labels) vs **golden Spec / compiler defaults 10/20**.
2. `signal_engine.py` display keys always `"EMA20"/"EMA60"` while using `self.fast`/`self.slow`.
3. Official Backtest↔Paper SSOT via `require_nautilus_runtime_params` — **parity tests PASS** (20 focused tests including parity).
4. Factor Lab backtest path does **not** share Nautilus Spec semantics (expected dual-stack).

```text
BACKTEST_PAPER_SHARED_SPEC=PASS   # Nautilus official path only (tests)
STRATEGY_SEMANTIC_DRIFT=PARTIAL   # UX/label/example drift YES; Spec→Paper SSOT NO hard drift found
```

### TOP_LEGACY_DEBT

1. `paper_orders` + `/execution/paper/*` mastery path.
2. QMT/vn.py residual adapter + Settings credential fields.
3. `engine/paper/sandbox_runtime.py` scaffold (not official).
4. Vectorized backtest remains primary Factor Lab path (KEEP for Research OS; not delete).
5. Closure/tmp artifacts (`tmp/`, `data/paper_runs/_*`) clutter — ARCHIVE candidates only (not deleted in QLN-0).

---

## 4. Phase 6 real state (recomputed)

```text
PHASE_6_CURRENT_REAL_STATE=WORKSTATION_STRONG / PRODUCTION_FRESHNESS_UNVERIFIED
```

| Area | Current evidence | Disposition |
|---|---|---|
| PaperRun model + migration 0032 | Present; local Alembic `0032_paper_runs` single head | PASS (local) |
| paper_runner + paper_node | Present | PASS |
| Spec SSOT runtime_params | Present; parity tests PASS | PASS |
| Kill / recovery / golden scripts | `scripts/phase6_golden_e2e.py`, recovery scripts exist | PRESENT; not re-run full E2E this session |
| LIVE deny | `quantlab_live=False`; create raises | PASS |
| Official path docs | Updated with QLN numbering note | PASS |
| Historical claim FINAL_ACCEPTANCE=20/20 | Document claim only | **DO NOT INHERIT** without fresh prod matrix |
| Prod deploy @ bf935a0 | Ancestor of HEAD; public health 200 | **PARTIAL** |

---

## 5. Database / migration

```text
MULTIPLE_HEADS=NO
LOCAL_HEAD=0032_paper_runs
LOCAL_CURRENT=0032_paper_runs
MIGRATION_DRIFT=NO   # local repo ↔ local DB
PRODUCTION_MIGRATION_TRUTH=NOT_RECHECKED_THIS_SESSION
HISTORICAL_DATA_PRESERVATION_RISK=MEDIUM
  (dual paper tables + soft-retired channel rows; deletion would lose history)
```

No upgrade/downgrade executed.

---

## 6. Test truth (summary)

```text
ENGINE_COLLECTED=136
BACKEND_COLLECTED=292
FOCUSED_PARITY_VALIDATION_PAPER=20 passed
FULL_SUITE_RERUN_THIS_SESSION=NO
NO_SILENT_TEST_LOSS=UNKNOWN_WITHOUT_BASELINE_DIFF
  (alembic_0032 + paper_runs tests still present in git)
```

See [Test Truth Ledger](./QUANTLAB_QLN0_TEST_TRUTH_LEDGER.md).

---

## 7. Production truth

```text
PRODUCTION_TRUTH=PARTIAL
PUBLIC_HEALTH=https://q.ziyingke.com/health → 200 {"status":"ok"}
DOCUMENTED_PROD_COMMIT=bf935a0
REPO_HEAD=29078ad (12 commits ahead; includes governance + closure fixes)
SSH_DEEP_PROBE_THIS_SESSION=NOT_PERFORMED
PRODUCTION_WRITE=DENY
```

---

## 8. Security boundary

```text
REAL_MONEY_ESCAPE_PATH_FOUND=NO_ACTIVE
REAL_MONEY_RESIDUAL_CODE=YES  # soft-retired gateway HTTP + Settings fields
QUANTLAB_LIVE_DEFAULT=False
PAPER_CREATE_BLOCKS_LIVE=YES
AI_DIRECT_LIVE=DENY (architecture docs + builder live_denied patterns)
BROWSER_BROKER_SECRET_PATH=NOT_FOUND_IN_ACTIVE_FE
```

If residual gateway code were re-enabled without Owner Gate → P0. Current ACTIVE routes DENY new QMT/vn.py.

---

## 9. Constitution / commercial alignment

```text
CONSTITUTION_ALIGNMENT=PARTIAL
  Evidence/kill/promote foundations exist in prototype form;
  Experiment Ledger / Spec v2 / Shadow Twin / Passport largely ABSENT → map to QLN-2..12
PRODUCT_VALUE_ALIGNMENT=MIXED
  Strategy Validation batch_001 correctly REJECTED=10 (good doctrine signal);
  AI Create Strategy nav still prominent vs Pre-Capital Review wedge
```

---

## 10. QLN-1 entry recommendation (NOT started)

```text
QLN_1_READY=YES_FOR_OWNER_DECISION
QLN_1_STARTED=NO
```

**If Owner later approves QLN-1**, first batch should be domain foundation only:

### P0 for QLN-1 (when authorized)

1. Canonical domain IDs / enums: Strategy lifecycle, Evidence stage, Environment, Execution mode.
2. Single vocabulary for Backtest vs Paper vs legacy paper_orders (mapping table; no merge yet).
3. Hash policy stubs + immutable identifiers for Spec/Experiment (schema contracts + tests).
4. Documented legacy mapping: Factor Lab results ≠ Nautilus Evidence.
5. Fail-closed rules: LIVE/Shadow remain DENY.

### Explicitly NOT to build yet

- Spec v2 full rewrite (QLN-2)
- Experiment Ledger implementation (QLN-3)
- Paper rewrite (QLN-5)
- AI expansion (QLN-6)
- Shadow/Live (QLN-8+)
- Marketplace / commercialization (QLN-12)
- Deleting legacy Factor Lab or paper_orders

### Owner Decision Cards (only if Owner wants structural calls)

| ID | Question | Default if silence |
|---|---|---|
| OD-1 | Keep Factor Lab vectorized backtest indefinitely as Research OS? | KEEP (recommended) |
| OD-2 | Soft-retire FE entry to legacy `/execution/paper/orders` in a later QLN? | HOLD until QLN-5 |
| OD-3 | Delete vs archive `_route_gateway` residual? | SOFT_RETIRE preserve until QLN-9 |
| OD-4 | Authorize production Paper freshness re-probe (read-only SSH)? | Optional; not required for QLN-1 domain work |

---

## 11. Acceptance checklist

| Criterion | Result |
|---|---|
| CURRENT_ARCHITECTURE_MAPPED | YES |
| LEGACY_ROADMAP_RECONCILED | YES |
| CAPABILITY_ASSET_LEDGER | COMPLETE |
| ARCHITECTURE_FRAGMENTATION_AUDITED | YES |
| STRATEGY_SEMANTIC_AUDIT | COMPLETE |
| EXPERIMENT_EVIDENCE_AUDIT | COMPLETE |
| VALIDATION_AUDIT | COMPLETE |
| PAPER_SANDBOX_RECONCILED | YES |
| DATABASE_MIGRATION_RECONCILED | YES (local); prod PARTIAL |
| TEST_TRUTH_RECONCILED | YES |
| PRODUCTION_TRUTH | EXPLICITLY_PARTIAL |
| SECURITY_BOUNDARY_AUDITED | YES |
| CONSTITUTION_GAP_LEDGER | COMPLETE |
| PRODUCT_VALUE_ALIGNMENT | ASSESSED |
| QLN_1_ENTRY_RECOMMENDATION | COMPLETE |
| UNAUTHORIZED_CHANGE | NO |

```text
QLN_0=PASS
STOP_REASON=APPROVED_SCOPE_COMPLETE
OWNER_DECISION_REQUIRED=YES  # only for optional OD cards / QLN-1 GO
NEXT_PHASE_AUTO_ENTER=NO
QLN_1_STARTED=NO
```

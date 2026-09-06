# QUANTLAB_QLN0_CAPABILITY_ASSET_LEDGER

```text
DOCUMENT=QUANTLAB_QLN0_CAPABILITY_ASSET_LEDGER
PHASE=QLN-0
MODE=READ_ONLY
ACTION=CLASSIFY_ONLY
EXECUTION_OF_CLASS_ACTIONS=DENY
THIS_ROUND_ENGINEERING=NO
FORMAL_CLOSURE_PATCH=YES
LEDGER_STATUS=COMPLETE
SOURCE_EVIDENCE=QLN-0 audit (CODE_TRUTH + TEST_TRUTH + DB_TRUTH + DOCUMENT_TRUTH)
NOTE=
  A late explore-agent summary said "Capability Ledger not created yet".
  That statement was STALE relative to this canonical file and is SUPERSEDED.
  Canonical path: docs/governance/qln0/QUANTLAB_QLN0_CAPABILITY_ASSET_LEDGER.md
```

Classification vocabulary (exactly one per row):

`KEEP` | `HARDEN` | `MERGE` | `MIGRATE` | `SOFT_RETIRE` | `ARCHIVE`

| ID | Asset | Path / evidence | Class | Current role | Canonical status | Still callable? | Constitution relation | Future QLN | Main risk | Build this round |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | Factor Lab / Research OS | `engine/factor_engine.py`, factors/projects/seasons APIs, Academy | KEEP | Research behavior + factor competition product | ACTIVE Research OS | YES | Preserved historical asset; not Strategy Evidence OS core alone | QLN-1 map; QLN-6 memory later | Confusing Research OS metrics with Evidence | NO |
| A02 | Legacy vectorized backtest | `engine/backtest.py`, Celery `/backtests` | KEEP | Factor Lab signal×OHLCV backtests | ACTIVE (Research path) | YES | Parallel to Nautilus Evidence path; must not silently equal Spec Evidence | Keep; map in QLN-1 | Dual metric worlds | NO |
| A03 | Nautilus backtest | `engine/nautilus/backtest_adapter.py` | KEEP | Official Spec golden / compiled EMA backtest | ACTIVE official BT | YES (if nautilus installed) | Kernel adapter for Evidence backtest | HARDEN later QLN-3/4 logging | Env/install dependent | NO |
| A04 | Strategy Spec v1 | `engine/strategies/spec.py`, `strategy_specs/` | MIGRATE | Canonical Spec truth v1 (YAML/JSON) | ACTIVE v1; not v2 | YES | Spec is Constitution truth; v1 incomplete vs Spec v2 | QLN-2 | Spec not DB-first-class | NO |
| A05 | Spec compiler | `engine/strategies/compiler.py` | HARDEN | Spec → Nautilus params (ema_cross) | ACTIVE | YES | Adapter compiler boundary | QLN-2 | Silent defaults 10/20; template-limited | NO |
| A06 | Runtime params SSOT | `engine/strategies/runtime_params.py` | KEEP | Shared Backtest+Paper params | ACTIVE SSOT | YES | Prevents Spec semantic drift on official path | QLN-2/5 | Bypass via non-official paths | NO |
| A07 | AI NL→Spec builder | `engine/ai/strategy_builder.py`, `/ai/strategy-builder` | HARDEN | Draft Spec from Chinese NL | ACTIVE (flagged) | YES | Amendment: multiplier not product body; live denied | QLN-6 | Generator UX over Evidence wedge | NO |
| A08 | AI MVP pipeline | `engine/ai/mvp_pipeline.py` | HARDEN | NL→gate→BT→validation glue | ACTIVE | YES | Research assist only | QLN-6 | Param default/fallback drift | NO |
| A09 | Validation (Spec decision) | `engine/validation/decision.py`, `pipeline.py` | HARDEN | PROMOTE/HOLD/REJECT gates | ACTIVE prototype | YES | Evidence Pipeline precursor (P0-A) | QLN-4 | Not full product Pre-Capital Review | NO |
| A10 | OOS | `engine/walk_forward.py` holdout + validation pipeline | KEEP | Out-of-sample evaluation | ACTIVE | YES | Constitution Evidence stage | QLN-4 | Factor path ≠ Spec path | NO |
| A11 | Walk Forward | `engine/walk_forward.py` folds + Spec validation | KEEP | Walk-forward robustness | ACTIVE | YES | Constitution Evidence stage | QLN-4 | Same dual-path split | NO |
| A12 | Data Gate | `engine/data/data_gate.py` | HARDEN | Pre-backtest data quality gate | ACTIVE partial | YES | Precursor to Data Trust Gate §11 | QLN-3 | Not mandatory everywhere | NO |
| A13 | PaperRun (model/service/API) | `backend/app/models/paper_run.py`, `paper_run_service.py`, `/paper-sandbox/*` | KEEP | Official paper sandbox persistence + control | ACTIVE official Paper | YES | Maps to Paper evidence stage; LIVE DENY | QLN-5 harden/close | Dual paper confusion | NO |
| A14 | paper_runner | `scripts/paper_runner.py` | KEEP | Spawns Nautilus paper process | ACTIVE official | YES | Execution path under Spec SSOT | QLN-5 | Process ownership / recovery ops | NO |
| A15 | paper_node | `engine/nautilus/paper_node.py` | KEEP | Nautilus TradingNode + sandbox exec | ACTIVE official | YES | Kernel paper adapter | QLN-5/8 | Data-client boundary vs exec | NO |
| A16 | Paper helpers (risk/kill/eval/portfolio) | `engine/paper/{risk_policy,kill_switch,evaluation,portfolio,gates,...}.py` | HARDEN | Paper risk, kill, eval, equity | ACTIVE | YES | Reality/divergence precursors | QLN-5 | Incomplete vs Experiment Ledger | NO |
| A17 | sandbox_runtime scaffold | `engine/paper/sandbox_runtime.py` | SOFT_RETIRE | Non-official paper scaffold | NON-CANONICAL | YES in tests only | Must not be treated as Paper Evidence | QLN-5 retire/archive | False second paper kernel | NO |
| A18 | Legacy paper_orders | `backend/app/models/execution.py`, `/execution/paper/*` | SOFT_RETIRE | Mastery/coaching paper orders | LEGACY_COMPAT | YES (paper channel) | Not official Evidence Paper | QLN-5 | Dual UX / false track record | NO |
| A19 | Factor PaperSnapshot | `backend/app/models/paper.py` | KEEP | Factor daily NAV tracking | ACTIVE Research | YES (Celery) | Research OS paper decay track ≠ Spec Paper | Map QLN-1; later MERGE decision | Name collision “paper” | NO |
| A20 | execution_adapter | `engine/execution_adapter.py` | SOFT_RETIRE | Channel routing; QMT/vn.py deny | SOFT_RETIRED + residual | Module YES; route_* raise | Secret/Live boundary residue | QLN-9 | Latent `_route_gateway` HTTP | NO |
| A21 | QMT residual | Settings `qmt_*`, adapter CHANNEL_QMT, docs | SOFT_RETIRE | Historical channel; NEW_CREATE=DENY | SOFT_RETIRED | Create NO; history YES | Non-goal: no broker reinvention | QLN-9 | Credential fields remain | NO |
| A22 | vn.py residual | `archive/legacy_vnpy`, import tools, adapter CHANNEL_VNPY | ARCHIVE | Historical engine; NEW_CREATE=DENY | ARCHIVED / soft-deny | Import YES; trade create NO | Kernel replaced by Nautilus | Keep archive; no revive | Accidental re-enable | NO |
| A23 | Risk paths (paper + execution preflight) | `engine/paper/risk_policy.py`, `execution_risk.py`, kill switch | HARDEN | Paper/runtime risk checks | ACTIVE partial | YES | Not Portfolio Governor; invariants incomplete | QLN-5/7/9 | Fragmented risk authority | NO |
| A24 | Portfolio optimize (L4) | `engine/portfolio.py`, `/portfolio` | KEEP | Research portfolio tools | ACTIVE research | YES | Not Constitution Portfolio Governor | QLN-7 | False diversification UX | NO |
| A25 | Regime modules | `engine/regime.py`, `regime_strategy.py` | KEEP | Regime research utilities | ACTIVE research | YES | Regime Layer precursor | QLN-4/6 | Not strategy forbidden-regime gate | NO |
| A26 | DB models (Research OS + paper + execution) | `backend/app/models/*` | KEEP | Persistence for product + paper | ACTIVE | YES | Domain vocabulary still multi-speak | QLN-1 | Orphan/legacy fields | NO |
| A27 | Migrations (incl. 0032 paper_runs) | `backend/migrations/versions/*` | KEEP | Schema history; local head 0032 | ACTIVE single head (local) | YES | Preserve history; no silent rewrite | QLN-1/5 | Prod freshness PARTIAL | NO |
| A28 | Frontend Research routes | `frontend-react` projects/factors/etc. | KEEP | Research OS UX | ACTIVE | YES | Usability layer (Amendment) | Later UX | UI≠Evidence | NO |
| A29 | Frontend AI strategy route | `/ai-strategy` | HARDEN | Generator entry | ACTIVE | YES | Doctrine: not hero surface | QLN-6 messaging | EMA 20/60 UX drift | NO |
| A30 | Frontend PaperTrading | `/paper` → paper-sandbox | KEEP | Official Paper UX | ACTIVE | YES | Paper evidence UI | QLN-5 | Dual with legacy panel | NO |
| A31 | Frontend legacy PaperExecutionPanel | L4 tools → `/execution/paper/orders` | SOFT_RETIRE | Legacy paper UX | LEGACY | YES | Compatibility only | QLN-5 | Dual paper path | NO |
| A32 | Workers / Celery / services | `backend/app/tasks/*`, paper_runner subprocess | KEEP | Async compute + paper process | ACTIVE | YES | Control/execution planes | QLN-1 ownership clarity | Beat still touches legacy sync | NO |
| A33 | Experiment foundations (project EXPERIMENT nodes, reports, hashes) | `project` graph, reports, `content_hash`, manifests | MIGRATE | Precursors only — not Experiment Ledger | PARTIAL foundations | YES | Constitution §9 incomplete | QLN-3 | Claiming “ledger exists” falsely | NO |
| A34 | Evidence foundations (lifecycle, validation, graveyard JSONL) | `lifecycle.py`, `validation/*`, graveyard file | MIGRATE | Partial Evidence Pipeline | PARTIAL | YES | §12 Evidence incomplete | QLN-4 | Promote without Paper evidence | NO |
| A35 | Strategy Graveyard (file JSONL) | `engine/validation/graveyard.py` | MIGRATE | Append-only rejects | PARTIAL | YES | §17 precursor | QLN-6 | Not queryable Research Memory | NO |
| A36 | Historical Phase 0–7 docs | `docs/nautilus-migration/` | KEEP | Factual historical route | HISTORICAL | N/A | Numbering superseded by QLN | — | Blind inheritance of PASS | NO |
| A37 | Governance Constitution + AE pack + Amendment 001 | `docs/governance/` | KEEP | WHY/BOUNDARY/ORDER + AE protocol | CANONICAL | N/A | SSOT | Amendments only by Owner | Scope creep | NO |
| A38 | Closure/tmp probe scripts | `scripts/_closure*`, `tmp/`, `data/paper_runs/_*` | ARCHIVE | Ops/debug evidence clutter | NON-PRODUCT | YES locally | Do not delete evidence casually | Clean later if Owner asks | Secret leakage in logs | NO |

## Coverage check (required topics)

| Required topic | Row IDs | Covered |
|---|---|---|
| Factor Lab / Research OS | A01 | YES |
| legacy vectorized backtest | A02 | YES |
| Nautilus backtest | A03 | YES |
| Strategy Spec | A04 | YES |
| compiler | A05 | YES |
| AI NL→Spec | A07 | YES |
| validation | A09 | YES |
| OOS | A10 | YES |
| Walk Forward | A11 | YES |
| Data Gate | A12 | YES |
| PaperRun | A13 | YES |
| paper runner | A14 | YES |
| legacy paper_orders | A18 | YES |
| execution_adapter | A20 | YES |
| sandbox_runtime scaffold | A17 | YES |
| QMT residual | A21 | YES |
| vn.py residual | A22 | YES |
| risk paths | A23 | YES |
| portfolio/regime | A24, A25 | YES |
| DB models/migrations | A26, A27 | YES |
| frontend routes | A28–A31 | YES |
| workers/services | A32 | YES |
| Experiment / Evidence foundations | A33–A35 | YES |

```text
CAPABILITY_ASSET_LEDGER=COMPLETE
CLASS_ACTIONS_EXECUTED=NO
QLN_0_ENGINEERING=NO
```

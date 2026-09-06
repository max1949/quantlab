# QUANTLAB_QLN0_CAPABILITY_ASSET_LEDGER

```text
PHASE=QLN-0
MODE=READ_ONLY
ACTION=CLASSIFY_ONLY
EXECUTION_OF_KEEP_HARDEN_MERGE=DENY
REPO_HEAD=29078ad
```

Classification vocabulary: `KEEP` | `HARDEN` | `MERGE` | `MIGRATE` | `SOFT_RETIRE` | `ARCHIVE`

| Asset | Path / evidence | Class | Notes |
|---|---|---|---|
| Legacy vectorized backtest | `engine/backtest.py` + Celery `/backtests` | KEEP | Research OS Factor Lab core; not Nautilus Evidence |
| Nautilus backtest adapter | `engine/nautilus/backtest_adapter.py` | KEEP / HARDEN | Official Spec backtest; golden tests |
| Strategy Spec v1 | `engine/strategies/spec.py`, `strategy_specs/` | KEEP / MIGRATE | Migrate → Spec v2 in QLN-2 (no action now) |
| Spec compiler | `engine/strategies/compiler.py` | KEEP / HARDEN | ema_cross only; silent defaults 10/20 |
| Runtime params SSOT | `engine/strategies/runtime_params.py` | KEEP | Backtest+Paper shared params |
| AI NL→Spec builder | `engine/ai/strategy_builder.py`, `/ai/strategy-builder` | KEEP / HARDEN | Multiplier not product core; live_denied |
| AI MVP pipeline | `engine/ai/mvp_pipeline.py` | HARDEN | Defaults on missing params — watch drift |
| Data Gate | `engine/data/data_gate.py` | KEEP / HARDEN | Exists; not full Constitution Data Trust |
| Validation stack (factor) | `engine/walk_forward.py`, `/validations` | KEEP | Factor Lab path |
| Validation stack (Spec) | `engine/validation/*` | KEEP / HARDEN | PROMOTE/HOLD/REJECT + graveyard prototype |
| Strategy Graveyard (file) | `engine/validation/graveyard.py`, `data/strategy_graveyard/` | KEEP / MIGRATE | JSONL; needs durable ledger later |
| PaperRun (official) | models/services/routes `paper_runs`, `paper_runner`, `paper_node` | KEEP / HARDEN | Phase 6 canonical runtime |
| Paper portfolio/eval/kill/recovery | `engine/paper/*.py` | KEEP / HARDEN | Official helpers |
| sandbox_runtime scaffold | `engine/paper/sandbox_runtime.py` | SOFT_RETIRE | Not official runner |
| Legacy paper_orders | `backend/app/models/execution.py`, `/execution/paper/*` | SOFT_RETIRE / KEEP | Mastery/coaching; NEW_FEATURES=DENY |
| Factor PaperSnapshot | `backend/app/models/paper.py` | KEEP | Separate paper tracking track |
| execution_adapter | `engine/execution_adapter.py` | SOFT_RETIRE / HARDEN | QMT/vn.py deny; residual HTTP |
| QMT residual | config + adapter + docs | SOFT_RETIRE | NEW_CREATE=DENY |
| vn.py residual | archive + adapter + tests | SOFT_RETIRE / ARCHIVE | Channel retired |
| Celery workers/tasks | `backend/app/tasks/*` | KEEP | Backtest/validation/paper/execution |
| DB models (research OS) | `backend/app/models/*` | KEEP | Users/factors/backtests/projects/… |
| Migration 0032 paper_runs | `backend/migrations/versions/0032_paper_runs.py` | KEEP | Local head |
| Frontend Research UI | `frontend-react/src/pages/*` | KEEP | Research OS |
| Frontend AI Create Strategy | `AiCreateStrategy` + nav | HARDEN | UX EMA examples drift; doctrine: not product core |
| Frontend PaperTrading | `/paper` → paper-sandbox API | KEEP | Official paper UX |
| Frontend legacy PaperExecutionPanel | execution paper orders | SOFT_RETIRE | Dual paper UX |
| Regime modules | `engine/regime.py`, `regime_strategy.py` | KEEP | Research utilities |
| Portfolio modules | `engine/portfolio.py`, paper portfolio | KEEP / HARDEN | Not Portfolio Governor |
| Research reports / graph | research services + models | KEEP | Research Memory precursor |
| Experiment Ledger | — | MIGRATE (gap) | Absent as Constitution asset → QLN-3 |
| Reality Score | — | MIGRATE (gap) | Absent → QLN-4 |
| Strategy Passport | — | MIGRATE (gap) | Absent → QLN-12 |
| Shadow Twin | — | MIGRATE (gap) | Absent → QLN-8 |
| Secrets plane | Settings env fields | HARDEN | No dedicated Secret Plane yet → QLN-9 |
| Closure/tmp probes | `scripts/_closure*`, `tmp/` | ARCHIVE | Ops leftovers; do not delete evidence casually |
| docs Phase 0–7 reports | `docs/nautilus-migration/` | KEEP | Historical facts |
| Constitution + AE pack | `docs/governance/` | KEEP | Canonical governance |

**QLN-0 action:** none beyond this ledger.

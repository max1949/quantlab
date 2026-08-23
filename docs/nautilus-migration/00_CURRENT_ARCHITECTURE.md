# 00 — Current Architecture (Phase 0)

**Freeze commit:** `bc981983f48987b8e90b08c4abfe3f282a12f2ea`  
**Branch:** `master`  
**Tag:** `phase0-freeze-bc98198`  
**Mode:** `QUANTLAB_NAUTILUS_EVOLUTION_MODE`  
**Date:** 2026-08-24  

## Verdict

QuantLab AI today is an **AI-assisted quantitative research platform** (Factor Lab + Validation + Research Reports + Growth OS), not yet an AI-native Quant OS. Trading execution is **paper-first** with optional HTTP gateway stubs labeled `vnpy` / `qmt`. There is **no installed `vnpy` Python package** and **no embedded VeighNa CtaEngine**. The research backtester is a **custom pandas/numpy signal engine** under `engine/`.

## Top-level layout

| Path | Role |
|------|------|
| `frontend-react/` | Primary UI (React + i18n ZH/EN) |
| `frontend/` | Legacy/static notes |
| `backend/` | FastAPI app, SQLAlchemy models, Alembic, Celery tasks |
| `engine/` | Pure compute: factors, backtest, OOS/WF, regime, data quality, execution adapter stubs |
| `sandbox/` | AST-guarded Python factor eval |
| `data/` | Parquet market data + README |
| `scripts/` | Ops / import / deploy helpers |
| `infra/` | DB init, deploy |
| `docs/` | Ops / recovery docs |
| `docker-compose.yml` | postgres / redis / backend / (optional workers) |

## Runtime stack (current)

```text
Browser (frontend-react)
        ↓ REST /api/v1
FastAPI (backend/app)
        ↓
SQLAlchemy + PostgreSQL
Redis + Celery (async backtest/validation)
        ↓
engine/*  (pandas/numpy/pyarrow)
        ↓
Parquet OHLCV under data/
```

## Application services (backend)

Mounted in `backend/app/api/v1/__init__.py`:

- Auth / Users / Me
- Factors / Backtests / Validations
- Research / Projects / Researchers / Feed
- Organizations / Challenges / Competition / Leaderboards
- AI
- Onboarding / Growth events
- Billing / Admin billing / Admin ops
- Portfolio
- Execution (paper + gateway channels)

## Compute engine (`engine/`) — reuse assets

| Module | Capability | Preserve? |
|--------|------------|-----------|
| `factor_engine.py` | Templates (momentum, SMA, RSI, vol, mean-reversion, …) + stack | YES |
| `formula_eval.py` / `python_eval.py` | L2/L3 factors | YES |
| `backtest.py` | Signal→position vectorized backtest + metrics | YES (legacy path; Nautilus becomes formal path) |
| `walk_forward.py` / `param_scan.py` / `segment_robustness.py` | Validation | YES |
| `regime.py` / `regime_strategy.py` | Vol regime | YES (extend, version later) |
| `data_quality.py` | OHLCV quality | YES (extend → DATA_GATE) |
| `research_quality.py` / `research_report.py` / `ai_advisor.py` | Research narrative / AI | YES |
| `execution_adapter.py` | paper/vnpy/qmt HTTP stub | MIGRATE (replace vnpy channel with Nautilus later) |
| `portfolio.py` / `cost_model.py` / `scoring.py` | Portfolio helpers / costs | YES |

## Data layer

- **Storage:** Parquet bars + PostgreSQL index (`data_snapshots`, market models)
- **Sources:** akshare continuous futures; optional **vn.py Mongo/SQLite import scripts** (data provenance = broker/venue specific when imported)
- **Quality:** `engine/data_quality.py` (gaps, zero volume, limit-lock bars)

## Research OS (preserve)

Core entities:

- `Factor` (template / stack / formula / python) + versioned `spec`
- `Backtest` (factor_id + snapshot + cost_config → metrics/equity/report)
- `Validation` (OOS + walk-forward + sensitivity + robustness)
- `ResearchReport` (narrative + `based_on` lineage)
- `ResearchProject` / tasks / academy / share / feed

**Note:** There is no separate TMOS-style `Evidence`/`Claim` table in QuantLab; lineage lives in `ResearchReport.based_on` and validation payloads. Preserve and extend rather than rewrite.

## What is NOT present yet

- Strategy Specification schema / versioning
- NautilusTrader dependency / adapter layer
- Spec compiler / golden Nautilus strategies
- Live broker adapters as first-class product (LIVE = DENY for MVP)
- UI modes SIMPLE / PROFESSIONAL / DEVELOPER as named product modes

## Target boundary (decision — not implemented in Phase 0)

```text
UI → Application Services → QuantLab Trading Abstraction → Nautilus Adapter → NautilusTrader
```

Business code must not mass-import Nautilus types.

## Incident during freeze

Working tree had **accidental zero-byte truncation** of:

- `README.md`, `engine/backtest.py`, `engine/__init__.py`, `docker-compose.yml`, `backend/migrations/env.py`

**Action:** restored from `HEAD` (`bc98198`) before inventory. No production DB touched.

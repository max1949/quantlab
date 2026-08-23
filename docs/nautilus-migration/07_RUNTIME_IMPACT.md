# 07 — Runtime Impact (Phase 0)

## Current runtime

| Component | Where | Notes |
|-----------|-------|-------|
| API | FastAPI / uvicorn | Port governance health: 8010 |
| DB | PostgreSQL 16 | docker-compose |
| Cache/queue | Redis 7 + Celery | async jobs |
| Compute | pandas/numpy/pyarrow | in-process + workers |
| Market data | Parquet on disk | `data/` |
| vn.py | **Not running** | optional HTTP URL; default stub |
| Nautilus | **Not installed** | Phase 1+ |

## Target runtime split

| Host | Role |
|------|------|
| Windows / Cursor | IDE, AI coding, git |
| Ubuntu 24.04 LTS | Nautilus runtime, research, backtest, paper, live |

```text
NO requirement that full Nautilus stack runs on Windows for production.
```

## Feature flags (planned)

```text
QUANTLAB_NAUTILUS_ENGINE
QUANTLAB_STRATEGY_SPEC
QUANTLAB_AI_STRATEGY_BUILDER
QUANTLAB_NAUTILUS_BACKTEST
QUANTLAB_SANDBOX
QUANTLAB_LIVE = OFF (default forever until Gate 7)
```

## Phase 0 runtime actions

```text
NO_SERVICE_RESTART = TRUE
NO_PRODUCTION_DEPLOY = TRUE
```

Governance note: `PROJECT_AGENT_EXECUTION.quantlab = false`; production deploy requires human.

# 08 — Test Impact (Phase 0)

## Current pyramid (partial)

| Layer | Location | Notes |
|-------|----------|-------|
| Engine unit | `engine/tests/*` | Strong for factors/backtest/regime/quality |
| Backend API | `backend/tests/*` | Auth, research, execution, imports |
| CI | `.github/workflows/ci.yml` | Python 3.12 + postgres + redis + frontend build |

## Tests that mention vn.py

- `engine/tests/test_execution_adapter.py`
- `backend/tests/test_execution.py`
- `backend/tests/test_vnpy_mongo_import.py`
- `backend/tests/test_research_quality.py` (`import_vnpy_sqlite`)

These must keep passing until channel/import migration; then replace with:

- paper-only / nautilus adapter tests
- generic parquet import fixtures

## Required new suites (later)

```text
Unit / Integration / Golden Strategy / Parity / Regression / E2E / Failure
```

Golden strategies (min 5): EMA Trend, Breakout, Mean Reversion, Multi-Instrument, Stop/TP.

## Phase 0

```text
NO_TEST_CODE_CHANGE = TRUE
```

# Phase 6 Paper Sandbox Report

## Gate Summary

```
PHASE=6
STATUS=PASS

WORKSTATION=PASS (tests + golden E2E + migration 0032)
PRODUCTION=PASS (tmos-prod-hk /srv/quantlab @ bf935a0; alembic 0032; Golden E2E PASS 2026-08-25)
TARGET_SERVER=43.161.203.133 (tmos-prod-hk) — NOT Oracle /opt/quantlab
UPDATE_NOTE=update-oracle.sh targets /opt/quantlab; production deploy used lean sync to /srv/quantlab
STRATEGY_SEMANTIC_DRIFT=NO (SSOT: compile_spec → runtime_params)
BACKTEST_PAPER_SHARED_SPEC=PASS
ALEMBIC_0032=PASS (upgrade / downgrade / re-upgrade)
SANDBOX_HARD_ISOLATION=PASS
PAPER_RUNTIME=PASS (Nautilus TradingNode + SandboxExecutionClient)
REALTIME_DATA=PASS (synthetic + binance_public factory)
PNL_EQUITY=PASS (portfolio.py equity curve + performance_summary)
BACKTEST_VS_PAPER=PASS (parity_status)
RESEARCH_FEEDBACK=PASS (PaperEvaluation → PaperRunEvent)
KILL_SWITCH=PASS
RESTART_RECOVERY=PASS (scripts/recovery_e2e.py)
GOLDEN_E2E=PASS (scripts/phase6_golden_e2e.py)
OFFICIAL_EXECUTION_PATH=NAUTILUSTRADER (see OFFICIAL_EXECUTION_PATH.md)
LEGACY paper_orders=COMPATIBILITY_ONLY
LIVE=DENY
REAL_MONEY_ORDER_COUNT=0
PHASE_7_AUTO_ENTER=DENY
NEXT_MODE=STRATEGY_VALIDATION
```

## Evidence commands (workstation PowerShell)

```powershell
cd C:\Users\Administrator\quantlab
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m pytest backend/tests/test_alembic_0032_paper_runs.py engine/tests/test_strategy_spec_parity.py backend/tests/test_paper_runs.py engine/tests/test_phase6_paper_sandbox.py backend/tests/test_execution.py -q
.\.venv\Scripts\python.exe scripts\phase6_golden_e2e.py
.\.venv\Scripts\python.exe scripts\recovery_e2e.py
```

## Architecture Delivered

- Strategy Spec SSOT: `engine/strategies/runtime_params.py`
- Portfolio: `engine/paper/portfolio.py`
- Evaluation: `engine/paper/evaluation.py`
- Official path: PaperRun → paper_runner → paper_node (Nautilus)
- Legacy execution: READ_ONLY compatibility, NEW_FEATURES=DENY

## NEXT

```
PHASE_7=DENY (Owner gate only)
ENGINEERING_MODE=MAINTENANCE_ONLY
STRATEGY_VALIDATION_MODE=ACTIVE
```

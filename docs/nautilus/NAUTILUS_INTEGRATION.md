# NautilusTrader Integration (Phase 1)

## Pin

See `config/nautilus-version.yaml` → **1.231.0** (released).  
Nightly / 2.0.0rc* / floating versions: **DENIED**.

## Install (workstation)

```powershell
# PowerShell @ repo root
python -m venv .venv-nautilus
.\.venv-nautilus\Scripts\pip install -r backend\requirements-nautilus.txt
$env:PYTHONPATH = (Get-Location).Path
.\.venv-nautilus\Scripts\python.exe -m pytest engine\tests\test_nautilus_golden_backtest.py -q
```

Production / paper / live runtime target remains **Ubuntu 24.04 + Python 3.12**.

## Architecture

```text
Application → engine.trading (abstractions) → engine.nautilus (adapter) → nautilus_trader
```

Do not import `nautilus_trader` from `backend/app/services/*`.

## Feature flags

Env / Settings (default all false):

- `QUANTLAB_NAUTILUS_ENGINE`
- `QUANTLAB_STRATEGY_SPEC`
- `QUANTLAB_AI_STRATEGY_BUILDER`
- `QUANTLAB_NAUTILUS_BACKTEST`
- `QUANTLAB_SANDBOX`
- `QUANTLAB_LIVE` (must stay OFF until Gate 7)

## Golden strategy

`golden_01_ema_trend` / `v1` — EMA cross on synthetic EUR/USD 15m bars.

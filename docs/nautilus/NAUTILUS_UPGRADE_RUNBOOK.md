# Nautilus Upgrade Runbook

1. Do **not** upgrade casually. Current pin: **1.231.0**.
2. Open a dedicated change with Gate checklist:
   - unit / integration / golden strategies / adapter / serialization
3. Install candidate only in `.venv-nautilus` first.
4. Diff release notes / breaking changes.
5. Run:
   ```powershell
   $env:PYTHONPATH=(Get-Location).Path
   .\.venv-nautilus\Scripts\python.exe -m pytest engine/tests/test_nautilus_golden_backtest.py engine/tests/test_phase5_research_loop.py -q
   ```
6. Update `config/nautilus-version.yaml` + `backend/requirements-nautilus.txt` only after PASS.
7. Reject `2.0.0rc*` / nightly for production until Gate says otherwise.

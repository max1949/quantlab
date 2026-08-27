#!/usr/bin/env bash
set -euo pipefail
echo "=== FLAGS FULL QUANTLAB ==="
sudo grep -E 'QUANTLAB_|AI_ENABLED|LLM_|LIVE|REAL_MONEY|PHASE' /srv/quantlab/.env 2>/dev/null \
  | sed -E 's/(KEY|SECRET|PASSWORD|TOKEN)=.*/\1=***/' || echo 'NO_MATCH'
echo "=== ALL ENV KEYS (names only) ==="
sudo grep -E '^[A-Z]' /srv/quantlab/.env 2>/dev/null | cut -d= -f1 | sort -u
echo "=== UNIT ==="
sudo systemctl cat quantlab.service | head -45
echo "=== WORKER ==="
sudo systemctl cat quantlab-worker.service | head -30
echo "=== NGINX ==="
sudo cat /etc/nginx/sites-available/q.ziyingke.com | head -80
echo "=== FRONTEND ==="
ls -la /srv/quantlab/frontend-react/dist/ | head -12
ls /srv/quantlab/frontend-react/dist/assets | head -8
echo "=== NAUTILUS ==="
/srv/quantlab/.venv/bin/python -c 'import nautilus_trader; print(nautilus_trader.__version__)'
echo "=== AI BUILDER UNAUTH ==="
curl -s -o /tmp/ai_sb.json -w "http:%{http_code}\n" \
  -X POST http://127.0.0.1:8010/api/v1/ai/strategy-builder \
  -H 'Content-Type: application/json' \
  -d '{"text":"test"}'
head -c 300 /tmp/ai_sb.json; echo
echo "=== SETTINGS RUNTIME ==="
cd /srv/quantlab
set -a; source .env; set +a
export PYTHONPATH=/srv/quantlab
/srv/quantlab/.venv/bin/python - <<'PY'
from backend.app.core.config import get_settings
s = get_settings()
print("app_env", s.app_env)
print("ai_enabled", s.ai_enabled)
print("quantlab_ai_strategy_builder", s.quantlab_ai_strategy_builder)
print("quantlab_nautilus_engine", s.quantlab_nautilus_engine)
print("quantlab_strategy_spec", s.quantlab_strategy_spec)
print("quantlab_nautilus_backtest", s.quantlab_nautilus_backtest)
print("quantlab_sandbox", s.quantlab_sandbox)
print("quantlab_live", s.quantlab_live)
print("llm_configured", bool(getattr(s, "llm_api_key", None)))
PY
echo "=== DB TABLES SAMPLE ==="
sudo -u postgres psql -d quantlab -c "\dt quantlab.*" 2>/dev/null | head -60

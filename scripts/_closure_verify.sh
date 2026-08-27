#!/bin/bash
cd /srv/quantlab
set -a; source .env; set +a
PYTHONPATH=/srv/quantlab .venv/bin/python - <<'PY'
from backend.app.core.config import get_settings
get_settings.cache_clear()
s = get_settings()
print("APP_ENV", s.app_env)
print("AI_BUILDER", s.quantlab_ai_strategy_builder)
print("LIVE", s.quantlab_live)
print("NAUTILUS", s.quantlab_nautilus_engine)
PY
# API gate smoke without auth should be 401 not 403
code=$(curl -s -o /tmp/sb.json -w "%{http_code}" -X POST http://127.0.0.1:8010/api/v1/ai/strategy-builder -H 'Content-Type: application/json' -d '{"text":"test"}')
echo "strategy-builder_noauth=$code"
cat /tmp/sb.json; echo
# dist asset present?
ls /srv/quantlab/frontend-react/dist/assets | head -5
grep -o 'index-[^"]*\.js' /srv/quantlab/frontend-react/dist/index.html

#!/usr/bin/env bash
set -euo pipefail
echo "=== HOST ==="
hostname
whoami
echo "=== DIRS ==="
ls -d /srv/quantlab /opt/quantlab 2>/dev/null || true
echo "=== SERVICES ==="
systemctl is-active quantlab quantlab-worker redis-server postgresql nginx 2>/dev/null || true
systemctl is-enabled quantlab quantlab-worker 2>/dev/null || true
echo "=== DEPLOY ==="
cat /srv/quantlab/DEPLOY_COMMIT 2>/dev/null || echo NO_DEPLOY_COMMIT
cat /srv/quantlab/DEPLOYED_AT 2>/dev/null || true
echo "=== PING ==="
curl -s http://127.0.0.1:8010/api/v1/ping; echo
curl -s -o /dev/null -w "health:%{http_code}\n" http://127.0.0.1:8010/health
echo "=== FLAGS ==="
sudo grep -E '^(APP_ENV|AI_ENABLED|LLM_|QUANTLAB_|CELERY_TASK|EXECUTION_KILL|RESEARCH_GATE|CAPTCHA)' /srv/quantlab/.env 2>/dev/null \
  | sed -E 's/(KEY|SECRET|PASSWORD|TOKEN)=.*/\1=***/; s#://[^:]+:[^@]+@#://***:***@#' || true
echo "=== ALEMBIC ==="
cd /srv/quantlab/backend
set -a
# shellcheck disable=SC1091
source /srv/quantlab/.env
set +a
export PYTHONPATH=/srv/quantlab
/srv/quantlab/.venv/bin/alembic current 2>&1 | tail -5
/srv/quantlab/.venv/bin/alembic heads 2>&1 | tail -3
echo "=== UNIT ==="
systemctl cat quantlab.service 2>&1 | head -40
echo "=== WORKER ==="
systemctl cat quantlab-worker.service 2>&1 | head -30
echo "=== NGINX ==="
sudo grep -E 'server_name|proxy_pass|root |listen' /etc/nginx/sites-available/q.ziyingke.com 2>/dev/null | head -40
echo "=== FRONTEND ==="
ls -la /srv/quantlab/frontend-react/dist/ 2>/dev/null | head -10
ls /srv/quantlab/frontend-react/dist/assets 2>/dev/null | head -8
echo "=== DB ==="
sudo -u postgres psql -d quantlab -tAc 'SELECT current_database()'
redis-cli ping
echo "=== NAUTILUS ==="
/srv/quantlab/.venv/bin/python -c 'import nautilus_trader; print(nautilus_trader.__version__)' 2>&1 || true
echo "=== AI BUILDER PROBE ==="
# unauth should be 401/403 not 404
curl -s -o /tmp/ai_sb.json -w "ai_builder_http:%{http_code}\n" \
  -X POST http://127.0.0.1:8010/api/v1/ai/strategy-builder \
  -H 'Content-Type: application/json' \
  -d '{"text":"test"}' || true
head -c 200 /tmp/ai_sb.json; echo

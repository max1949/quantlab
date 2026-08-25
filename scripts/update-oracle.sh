#!/usr/bin/env bash
# =============================================================================
# LEGACY_ORACLE_DEPLOY_SCRIPT=DEPRECATED
# TENCENT_PRODUCTION_USE=DENY
#
# This script targets the LEGACY Oracle host path (/opt/quantlab).
# It must NEVER be used for Tencent production:
#   PRODUCTION_SERVER=43.161.203.133
#   PRODUCTION_PATH=/srv/quantlab
#
# Do not run this against Tencent prod. Maintenance-only; Strategy Validation
# mode does not authorize new deploy tooling.
# =============================================================================
# Oracle 生产机一键更新代码并重启 (避免 git pull 与 scp dist 冲突)
# 用法: sudo bash /opt/quantlab/scripts/update-oracle.sh
#
# 两阶段执行: 先 pull 最新脚本, 再 exec 自身以运行含 alembic 的新版逻辑。
set -euo pipefail

if [[ "${QUANTLAB_FORCE_LEGACY_ORACLE:-}" != "1" ]]; then
  echo "ERROR: scripts/update-oracle.sh is DEPRECATED for Tencent production." >&2
  echo "  LEGACY_ORACLE_DEPLOY_SCRIPT=DEPRECATED" >&2
  echo "  TENCENT_PRODUCTION_USE=DENY" >&2
  echo "  PRODUCTION_PATH=/srv/quantlab (not /opt/quantlab)" >&2
  echo "Set QUANTLAB_FORCE_LEGACY_ORACLE=1 only on the legacy Oracle host." >&2
  exit 2
fi

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
cd "$INSTALL_DIR"

if [[ "${QUANTLAB_UPDATE_PHASE:-}" != "post-pull" ]]; then
  export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -i /root/.ssh/quantlab_deploy -o IdentitiesOnly=yes}"
  git fetch origin
  git reset --hard origin/master
  export QUANTLAB_UPDATE_PHASE=post-pull
  exec bash "$INSTALL_DIR/scripts/update-oracle.sh"
fi

echo "==> alembic upgrade"
export PYTHONPATH="$INSTALL_DIR"
source "$INSTALL_DIR/.venv/bin/activate"
set -a && source "$INSTALL_DIR/.env" && set +a
cd "$INSTALL_DIR/backend" && alembic upgrade head && cd "$INSTALL_DIR"

# 异步任务: 生产环境 Redis 不可用时直接失败, 避免重计算压回 API 进程
_redis_ok=false
if redis-cli ping 2>/dev/null | grep -q PONG; then
  _redis_ok=true
elif systemctl restart redis 2>/dev/null && sleep 2 && redis-cli ping 2>/dev/null | grep -q PONG; then
  _redis_ok=true
fi

if [[ "$_redis_ok" == true ]]; then
  cp "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.bak.$(date +%Y%m%d%H%M%S)"
  if grep -q '^CELERY_TASK_ALWAYS_EAGER=true' "$INSTALL_DIR/.env" 2>/dev/null; then
    sed -i 's/^CELERY_TASK_ALWAYS_EAGER=true/CELERY_TASK_ALWAYS_EAGER=false/' "$INSTALL_DIR/.env"
    echo "==> CELERY_TASK_ALWAYS_EAGER=false (Redis OK)"
  fi
  if [[ -f "$INSTALL_DIR/scripts/quantlab-worker.service" ]]; then
    APP_USER=$(stat -c '%U' "$INSTALL_DIR" 2>/dev/null || echo quantlab)
    sed "s/User=quantlab/User=${APP_USER}/" "$INSTALL_DIR/scripts/quantlab-worker.service" \
      > /etc/systemd/system/quantlab-worker.service
    systemctl daemon-reload
    systemctl enable quantlab-worker
    systemctl restart quantlab-worker
    echo "==> quantlab-worker restarted"
  fi
else
  if [[ "${APP_ENV:-production}" == "production" ]]; then
    echo "ERROR: Redis unavailable in production; aborting deploy to keep API workers isolated." >&2
    exit 1
  fi
  echo "==> Redis unavailable — development sync fallback only"
  systemctl stop quantlab-worker 2>/dev/null || true
  systemctl disable quantlab-worker 2>/dev/null || true
fi

systemctl restart quantlab
sleep 2

echo "==> health"
curl -sf "http://127.0.0.1:${QUANTLAB_PORT:-8010}/health"
echo ""

CRON_LINE="30 10 * * 1-5 bash ${INSTALL_DIR}/scripts/run-daily-paper.sh >> /var/log/quantlab-paper.log 2>&1"
if ! crontab -l 2>/dev/null | grep -qF run-daily-paper; then
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "==> installed daily paper cron"
fi

DERIVED_CRON="45 10 * * 1-5 bash ${INSTALL_DIR}/scripts/materialize-derived-timeframes.sh >> /var/log/quantlab-derived.log 2>&1"
if ! crontab -l 2>/dev/null | grep -qF materialize-derived-timeframes; then
  (crontab -l 2>/dev/null; echo "$DERIVED_CRON") | crontab -
  echo "==> installed derived timeframe cron"
fi

REVISIT_CRON="30 9 * * * bash ${INSTALL_DIR}/scripts/run-revisit-emails.sh >> /var/log/quantlab-revisit.log 2>&1"
if ! crontab -l 2>/dev/null | grep -qF run-revisit-emails; then
  (crontab -l 2>/dev/null; echo "$REVISIT_CRON") | crontab -
  echo "==> installed revisit email cron"
fi

echo "==> public feed (first 120 chars)"
curl -sf "http://127.0.0.1:${QUANTLAB_PORT:-8010}/api/v1/public/feed" | head -c 120
echo ""
echo "OK — $(git log -1 --oneline)"

#!/usr/bin/env bash
# Oracle 生产机一键更新代码并重启 (避免 git pull 与 scp dist 冲突)
# 用法: sudo bash /opt/quantlab/scripts/update-oracle.sh
#
# 两阶段执行: 先 pull 最新脚本, 再 exec 自身以运行含 alembic 的新版逻辑。
set -euo pipefail

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

echo "==> public feed (first 120 chars)"
curl -sf "http://127.0.0.1:${QUANTLAB_PORT:-8010}/api/v1/public/feed" | head -c 120
echo ""
echo "OK — $(git log -1 --oneline)"

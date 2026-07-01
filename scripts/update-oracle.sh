#!/usr/bin/env bash
# Oracle 生产机一键更新代码并重启 (避免 git pull 与 scp dist 冲突)
# 用法: sudo bash /opt/quantlab/scripts/update-oracle.sh
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
cd "$INSTALL_DIR"

export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -i /root/.ssh/quantlab_deploy -o IdentitiesOnly=yes}"
git fetch origin
git reset --hard origin/master

systemctl restart quantlab
sleep 2

echo "==> health"
curl -sf "http://127.0.0.1:${QUANTLAB_PORT:-8010}/health"
echo ""
echo "==> public feed (first 120 chars)"
curl -sf "http://127.0.0.1:${QUANTLAB_PORT:-8010}/api/v1/public/feed" | head -c 120
echo ""
echo "OK — $(git log -1 --oneline)"

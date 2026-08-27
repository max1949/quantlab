#!/usr/bin/env bash
# QuantLab functional-closure backup on tmos-prod-hk
set -euo pipefail
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACK="/opt/backups/quantlab-closure-${STAMP}"
sudo mkdir -p "$BACK"
sudo chown ubuntu:ubuntu "$BACK"

sudo -u postgres pg_dump -Fc quantlab -f "/tmp/quantlab_${STAMP}.dump"
sudo mv "/tmp/quantlab_${STAMP}.dump" "$BACK/quantlab.dump"
sudo chown ubuntu:ubuntu "$BACK/quantlab.dump"

sudo cp -a /srv/quantlab/.env "$BACK/env.bak"
sudo cp -a /etc/systemd/system/quantlab.service "$BACK/" 2>/dev/null || true
sudo cp -a /etc/systemd/system/quantlab-worker.service "$BACK/" 2>/dev/null || true
sudo cp -a /etc/nginx/sites-enabled/q.ziyingke.com "$BACK/nginx-q.ziyingke.com" 2>/dev/null || true
sudo chown -R ubuntu:ubuntu "$BACK"

{
  echo "PRE_DEPLOY_STAMP=$STAMP"
  echo "PRE_ALEMBIC=$(sudo -u postgres psql -d quantlab -tAc 'SELECT version_num FROM alembic_version;')"
  echo "PRE_DEPLOY_COMMIT=$(cat /srv/quantlab/DEPLOY_COMMIT 2>/dev/null || echo unknown)"
  echo "INSTALL_DIR=/srv/quantlab"
  echo "ROLLBACK=pg_restore dump + code_tree_pre.tgz + restore .env + systemctl restart quantlab quantlab-worker"
} > "$BACK/pre_deploy.txt"

sudo tar --exclude='.venv' --exclude='data/market_data' --exclude='data/paper_runs' \
  -czf "$BACK/code_tree_pre.tgz" -C /srv quantlab
sudo chown ubuntu:ubuntu "$BACK/code_tree_pre.tgz"

echo "BACKUP=PASS"
echo "BACKUP_PATH=$BACK"
echo "ROLLBACK_COMMAND=see $BACK/pre_deploy.txt"
cat "$BACK/pre_deploy.txt"
ls -lh "$BACK"

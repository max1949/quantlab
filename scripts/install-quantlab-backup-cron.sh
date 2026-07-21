#!/usr/bin/env bash
# Install daily + weekly QuantLab backup cron jobs on the production host.
# Usage: sudo bash /opt/quantlab/scripts/install-quantlab-backup-cron.sh
#
# Times offset from TMOS (03:20 / Sun 04:40) to avoid dump contention.
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
CRON_FILE="/etc/cron.d/quantlab-backup"
LOG_DIR="/var/log"
DAILY_MINUTE="${DAILY_MINUTE:-40}"
DAILY_HOUR="${DAILY_HOUR:-3}"
WEEKLY_MINUTE="${WEEKLY_MINUTE:-10}"
WEEKLY_HOUR="${WEEKLY_HOUR:-5}"
WEEKLY_DOW="${WEEKLY_DOW:-0}" # Sunday

chmod +x \
  "${INSTALL_DIR}/scripts/backup-quantlab.sh" \
  "${INSTALL_DIR}/scripts/restore-quantlab.sh" \
  "${INSTALL_DIR}/scripts/backup-quantlab-offsite-github.sh" \
  "${INSTALL_DIR}/scripts/restore-quantlab-from-github.sh" 2>/dev/null || true

cat > "$CRON_FILE" <<EOF
# QuantLab automated backups (managed by install-quantlab-backup-cron.sh)
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=""

# Daily at ${DAILY_HOUR}:${DAILY_MINUTE} (server local time)
${DAILY_MINUTE} ${DAILY_HOUR} * * * root /bin/bash ${INSTALL_DIR}/scripts/backup-quantlab.sh daily >> ${LOG_DIR}/quantlab-backup-daily.log 2>&1

# Weekly (${WEEKLY_DOW}=0 Sunday) at ${WEEKLY_HOUR}:${WEEKLY_MINUTE}
${WEEKLY_MINUTE} ${WEEKLY_HOUR} * * ${WEEKLY_DOW} root /bin/bash ${INSTALL_DIR}/scripts/backup-quantlab.sh weekly >> ${LOG_DIR}/quantlab-backup-weekly.log 2>&1
EOF

chmod 644 "$CRON_FILE"
systemctl reload crond 2>/dev/null || systemctl reload cron 2>/dev/null || true

echo "installed ${CRON_FILE}"
echo "daily  -> ${DAILY_HOUR}:${DAILY_MINUTE}  log=${LOG_DIR}/quantlab-backup-daily.log"
echo "weekly -> dow=${WEEKLY_DOW} ${WEEKLY_HOUR}:${WEEKLY_MINUTE}  log=${LOG_DIR}/quantlab-backup-weekly.log"
echo "manual: bash ${INSTALL_DIR}/scripts/backup-quantlab.sh"
echo "restore: QUANTLAB_RESTORE_CONFIRM=YES bash ${INSTALL_DIR}/scripts/restore-quantlab.sh --latest daily"

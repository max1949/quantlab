#!/usr/bin/env bash
# QuantLab one-click restore from a backup created by backup-quantlab.sh
#
# List:
#   sudo bash /opt/quantlab/scripts/restore-quantlab.sh --list
# Restore latest daily:
#   sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab.sh --latest daily
# Restore a stamp:
#   sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab.sh /opt/quantlab/backups/daily/20260721T160000Z
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/quantlab/backups}"
QUANTLAB_PORT="${QUANTLAB_PORT:-8010}"

usage() {
  cat <<'EOF'
Usage:
  restore-quantlab.sh --list
  restore-quantlab.sh --latest daily|weekly
  restore-quantlab.sh /path/to/backup-dir

Safety:
  Requires QUANTLAB_RESTORE_CONFIRM=YES
  Creates a pre-restore safety dump first.
EOF
}

list_backups() {
  echo "==> daily"
  ls -1dt "${BACKUP_ROOT}/daily"/*/ 2>/dev/null | head -20 || echo "(none)"
  echo "==> weekly"
  ls -1dt "${BACKUP_ROOT}/weekly"/*/ 2>/dev/null | head -20 || echo "(none)"
}

resolve_target() {
  local arg="${1:-}"
  if [[ "$arg" == "--latest" ]]; then
    local label="${2:-daily}"
    if [[ -L "${BACKUP_ROOT}/${label}/latest" || -d "${BACKUP_ROOT}/${label}/latest" ]]; then
      readlink -f "${BACKUP_ROOT}/${label}/latest"
      return
    fi
    ls -1dt "${BACKUP_ROOT}/${label}"/*/ 2>/dev/null | head -1 | sed 's:/*$::'
    return
  fi
  if [[ -d "$arg" ]]; then
    echo "$arg"
    return
  fi
  echo "ERROR: backup not found: $arg" >&2
  exit 1
}

if [[ "${1:-}" == "--list" || "${1:-}" == "-l" ]]; then
  list_backups
  exit 0
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

if [[ "${QUANTLAB_RESTORE_CONFIRM:-}" != "YES" ]]; then
  echo "ERROR: refusing restore without QUANTLAB_RESTORE_CONFIRM=YES" >&2
  usage
  exit 1
fi

TARGET="$(resolve_target "$@")"
if [[ -z "$TARGET" || ! -f "${TARGET}/quantlab.dump" ]]; then
  echo "ERROR: missing quantlab.dump in ${TARGET:-}" >&2
  exit 1
fi

if [[ -f "${TARGET}/quantlab.dump.sha256" ]]; then
  echo "==> verify checksum"
  (cd "$TARGET" && sha256sum -c quantlab.dump.sha256)
fi

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  echo "ERROR: missing ${INSTALL_DIR}/.env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "${INSTALL_DIR}/.env"
set +a

PG_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql:\/\/}"
PG_URL="${PG_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

safety_dir="${BACKUP_ROOT}/pre-restore/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$safety_dir"
chmod 700 "$safety_dir"
echo "==> safety dump before restore -> ${safety_dir}"
pg_dump --dbname="$PG_URL" --format=custom --file="${safety_dir}/quantlab.dump" || true
install -m 600 "${INSTALL_DIR}/.env" "${safety_dir}/.env" || true

echo "==> stop services"
systemctl stop quantlab quantlab-worker 2>/dev/null || true

echo "==> restore database (clean)"
pg_restore --dbname="$PG_URL" --clean --if-exists --no-owner --no-acl "${TARGET}/quantlab.dump"

if [[ -f "${TARGET}/.env" ]]; then
  echo "==> restore .env from backup (kept mode 600)"
  install -m 600 "${TARGET}/.env" "${INSTALL_DIR}/.env"
fi

echo "==> start services"
systemctl start quantlab
systemctl start quantlab-worker 2>/dev/null || true
systemctl is-active quantlab >/dev/null

echo "==> health"
ok=0
for _ in $(seq 1 45); do
  if out=$(curl -sf "http://127.0.0.1:${QUANTLAB_PORT}/health" 2>/dev/null); then
    if echo "$out" | grep -q '"status"[[:space:]]*:[[:space:]]*"ok"'; then
      ok=1
      break
    fi
  fi
  sleep 1
done
if [[ "$ok" -ne 1 ]]; then
  echo "ERROR: health check failed after restore" >&2
  systemctl --no-pager -l status quantlab quantlab-worker || true
  exit 1
fi

echo "restore_ok from=${TARGET}"
echo "safety_dump=${safety_dir}"
if [[ -f "${TARGET}/meta.txt" ]]; then
  cat "${TARGET}/meta.txt"
fi

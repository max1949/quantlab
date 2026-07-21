#!/usr/bin/env bash
# QuantLab production backup: Postgres + .env + git SHA.
# Usage:
#   sudo bash /opt/quantlab/scripts/backup-quantlab.sh
#   sudo bash /opt/quantlab/scripts/backup-quantlab.sh weekly
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/quantlab/backups}"
LABEL="${1:-daily}"
KEEP_DAILY="${KEEP_DAILY:-14}"
KEEP_WEEKLY="${KEEP_WEEKLY:-8}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out_dir="${BACKUP_ROOT}/${LABEL}/${stamp}"

mkdir -p "$out_dir"
chmod 700 "$BACKUP_ROOT" "${BACKUP_ROOT}/daily" "${BACKUP_ROOT}/weekly" 2>/dev/null || true
chmod 700 "$out_dir"

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  echo "ERROR: missing ${INSTALL_DIR}/.env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "${INSTALL_DIR}/.env"
set +a

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL not set" >&2
  exit 1
fi

# Convert SQLAlchemy URL → libpq URL for pg_dump.
PG_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql:\/\/}"
PG_URL="${PG_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

git_sha="unknown"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git_sha="$(git -C "$INSTALL_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
fi

echo "==> dump database"
pg_dump --dbname="$PG_URL" --format=custom --file="${out_dir}/quantlab.dump"
sha256sum "${out_dir}/quantlab.dump" > "${out_dir}/quantlab.dump.sha256"

echo "==> copy secrets + meta"
install -m 600 "${INSTALL_DIR}/.env" "${out_dir}/.env"
{
  echo "created_at_utc=${stamp}"
  echo "label=${LABEL}"
  echo "git_sha=${git_sha}"
  echo "host=$(hostname -f 2>/dev/null || hostname)"
  # Host only — never write full DATABASE_URL (contains password).
  echo "database_host=$(printf '%s' "$PG_URL" | sed -E 's#^[a-zA-Z0-9+.-]+://[^@]+@([^/:]+).*#\1#')"
} > "${out_dir}/meta.txt"
chmod 600 "${out_dir}/meta.txt"

# Pointer to latest for this label.
ln -sfn "${stamp}" "${BACKUP_ROOT}/${LABEL}/latest"

# Retention
if [[ "$LABEL" == "weekly" ]]; then
  find "${BACKUP_ROOT}/weekly" -mindepth 1 -maxdepth 1 -type d -mtime "+${KEEP_WEEKLY}" -exec rm -rf {} +
else
  find "${BACKUP_ROOT}/daily" -mindepth 1 -maxdepth 1 -type d -mtime "+${KEEP_DAILY}" -exec rm -rf {} +
fi

size="$(du -sh "$out_dir" | awk '{print $1}')"
echo "backup_ok label=${LABEL} stamp=${stamp} size=${size} git=${git_sha}"
echo "path=${out_dir}"

# Optional encrypted offsite upload (GitHub private Releases). No-op if not configured.
if [[ "${QUANTLAB_OFFSITE:-1}" != "0" ]]; then
  if [[ -f "${INSTALL_DIR}/scripts/backup-quantlab-offsite-github.sh" ]]; then
    bash "${INSTALL_DIR}/scripts/backup-quantlab-offsite-github.sh" "$out_dir" "$LABEL" || {
      echo "WARNING: local backup succeeded but offsite upload failed" >&2
      exit 1
    }
  fi
fi

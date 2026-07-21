#!/usr/bin/env bash
# One-time setup for encrypted GitHub offsite backups on the production host.
#
# Required env before running:
#   GITHUB_BACKUP_TOKEN   classic/fine-grained token with repo contents+releases on quantlab-backups
#   GITHUB_BACKUP_REPO    default max1949/quantlab-backups
#
# Usage:
#   sudo GITHUB_BACKUP_TOKEN=ghp_xxx bash /opt/quantlab/scripts/setup-quantlab-github-backup.sh
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
REPO="${GITHUB_BACKUP_REPO:-max1949/quantlab-backups}"
TOKEN="${GITHUB_BACKUP_TOKEN:-}"
KEY_FILE="${BACKUP_ENCRYPTION_KEY_FILE:-${INSTALL_DIR}/.backup_encryption_key}"
CONFIG="${INSTALL_DIR}/.backup_offsite.env"

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: set GITHUB_BACKUP_TOKEN before running" >&2
  exit 1
fi

chmod +x \
  "${INSTALL_DIR}/scripts/backup-quantlab.sh" \
  "${INSTALL_DIR}/scripts/backup-quantlab-offsite-github.sh" \
  "${INSTALL_DIR}/scripts/restore-quantlab.sh" \
  "${INSTALL_DIR}/scripts/restore-quantlab-from-github.sh" \
  "${INSTALL_DIR}/scripts/install-quantlab-backup-cron.sh"

if [[ ! -f "$KEY_FILE" ]]; then
  echo "==> generate encryption key"
  openssl rand -base64 48 > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
else
  echo "==> reuse existing encryption key ${KEY_FILE}"
fi

umask 077
cat > "$CONFIG" <<EOF
# Managed by setup-quantlab-github-backup.sh — do not commit
GITHUB_BACKUP_TOKEN=${TOKEN}
GITHUB_BACKUP_REPO=${REPO}
BACKUP_ENCRYPTION_KEY_FILE=${KEY_FILE}
KEEP_OFFSITE_RELEASES=16
EOF
chmod 600 "$CONFIG"

echo "==> verify GitHub access to ${REPO}"
code="$(curl -sS -o /tmp/quantlab_gh_check.json -w '%{http_code}' \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${REPO}")"
if [[ "$code" != "200" ]]; then
  echo "ERROR: cannot access ${REPO} (HTTP ${code})" >&2
  cat /tmp/quantlab_gh_check.json >&2 || true
  exit 1
fi
priv="$(python3 - <<'PY'
import json
print(json.load(open("/tmp/quantlab_gh_check.json")).get("private"))
PY
)"
if [[ "$priv" != "True" && "$priv" != "true" ]]; then
  echo "ERROR: ${REPO} must be a PRIVATE repository" >&2
  exit 1
fi

echo "==> test backup + offsite upload"
bash "${INSTALL_DIR}/scripts/backup-quantlab.sh" daily

echo ""
echo "setup_ok"
echo "config=${CONFIG}"
echo "key=${KEY_FILE}"
echo "IMPORTANT: copy ${KEY_FILE} to your PC offline. Without this key, cloud backups cannot be decrypted."
echo "Cloud repo: https://github.com/${REPO}/releases"

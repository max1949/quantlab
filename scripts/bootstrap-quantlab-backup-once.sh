#!/usr/bin/env bash
# Bootstrap QuantLab triple backup on production (run once on server).
set -euo pipefail
cd /opt/quantlab
export GIT_SSH_COMMAND='ssh -i /root/.ssh/quantlab_deploy -o IdentitiesOnly=yes'
git fetch origin
git reset --hard origin/master
chmod +x scripts/backup-quantlab.sh scripts/backup-quantlab-offsite-github.sh \
  scripts/setup-quantlab-github-backup.sh scripts/install-quantlab-backup-cron.sh \
  scripts/restore-quantlab.sh scripts/restore-quantlab-from-github.sh

TOKEN="$(grep '^GITHUB_BACKUP_TOKEN=' /opt/tmos/.backup_offsite.env | cut -d= -f2-)"
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: no token in /opt/tmos/.backup_offsite.env" >&2
  exit 1
fi

AUTH="Authorization: Bearer ${TOKEN}"
ACCEPT="Accept: application/vnd.github+json"
VER="X-GitHub-Api-Version: 2022-11-28"

echo "==> ensure private repo max1949/quantlab-backups"
code="$(curl -sS -o /tmp/ql_repo.json -w '%{http_code}' \
  -H "$AUTH" -H "$ACCEPT" -H "$VER" \
  https://api.github.com/repos/max1949/quantlab-backups || true)"
echo "repo_check_http=${code}"
if [[ "$code" == "404" ]]; then
  create_code="$(curl -sS -o /tmp/ql_repo_create.json -w '%{http_code}' \
    -X POST \
    -H "$AUTH" -H "$ACCEPT" -H "$VER" \
    -H "Content-Type: application/json" \
    https://api.github.com/user/repos \
    -d '{"name":"quantlab-backups","private":true,"description":"Encrypted QuantLab production backups only — no plaintext","auto_init":true}')"
  echo "repo_create_http=${create_code}"
  if [[ "$create_code" != "201" && "$create_code" != "200" ]]; then
    cat /tmp/ql_repo_create.json >&2 || true
    exit 1
  fi
elif [[ "$code" != "200" ]]; then
  cat /tmp/ql_repo.json >&2 || true
  exit 1
else
  echo "repo_exists"
fi

echo "==> setup github backup"
GITHUB_BACKUP_TOKEN="$TOKEN" GITHUB_BACKUP_REPO=max1949/quantlab-backups \
  bash /opt/quantlab/scripts/setup-quantlab-github-backup.sh

echo "==> install cron"
bash /opt/quantlab/scripts/install-quantlab-backup-cron.sh

echo "==> list local backups"
bash /opt/quantlab/scripts/restore-quantlab.sh --list | head -20
ls -la /opt/quantlab/.backup_encryption_key /opt/quantlab/.backup_offsite.env /etc/cron.d/quantlab-backup
echo BOOTSTRAP_OK

#!/usr/bin/env bash
# Download an encrypted GitHub offsite backup, decrypt, then restore.
#
# Usage:
#   sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab-from-github.sh daily
#   sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab-from-github.sh weekly
#   sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab-from-github.sh daily backup-daily-20260721T164731Z
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
CONFIG="${BACKUP_OFFSITE_ENV:-${INSTALL_DIR}/.backup_offsite.env}"
LABEL="${1:-daily}"
TAG="${2:-quantlab-${LABEL}-latest}"
ASSET_NAME="quantlab-${LABEL}-latest.tgz.enc"

if [[ "${QUANTLAB_RESTORE_CONFIRM:-}" != "YES" ]]; then
  echo "ERROR: refusing restore without QUANTLAB_RESTORE_CONFIRM=YES" >&2
  exit 1
fi
if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: missing ${CONFIG}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$CONFIG"
set +a

TOKEN="${GITHUB_BACKUP_TOKEN:-}"
REPO="${GITHUB_BACKUP_REPO:-}"
KEY_FILE="${BACKUP_ENCRYPTION_KEY_FILE:-${INSTALL_DIR}/.backup_encryption_key}"
API="${GITHUB_API:-https://api.github.com}"

if [[ -z "$TOKEN" || -z "$REPO" || ! -f "$KEY_FILE" ]]; then
  echo "ERROR: offsite token/repo/key incomplete" >&2
  exit 1
fi

# If restoring a stamped tag, asset name matches stamp.
if [[ "$TAG" == backup-${LABEL}-* ]]; then
  stamp="${TAG#backup-${LABEL}-}"
  ASSET_NAME="quantlab-${LABEL}-${stamp}.tgz.enc"
fi

work="$(mktemp -d /tmp/quantlab-restore-gh.XXXXXX)"
cleanup() { rm -rf "$work"; }
trap cleanup EXIT

export QL_OFFSITE_TOKEN="$TOKEN"
export QL_OFFSITE_REPO="$REPO"
export QL_OFFSITE_API="$API"
export QL_OFFSITE_TAG="$TAG"
export QL_OFFSITE_ASSET="$ASSET_NAME"
export QL_OFFSITE_OUT="${work}/${ASSET_NAME}"

python3 - <<'PY'
import json
import os
import urllib.parse
import urllib.request

token = os.environ["QL_OFFSITE_TOKEN"]
repo = os.environ["QL_OFFSITE_REPO"]
api = os.environ["QL_OFFSITE_API"].rstrip("/")
tag = os.environ["QL_OFFSITE_TAG"]
asset_name = os.environ["QL_OFFSITE_ASSET"]
out = os.environ["QL_OFFSITE_OUT"]
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "quantlab-offsite-restore",
}
req = urllib.request.Request(
    f"{api}/repos/{repo}/releases/tags/{urllib.parse.quote(tag)}",
    headers=headers,
)
with urllib.request.urlopen(req) as resp:
    release = json.load(resp)
asset = next((a for a in release.get("assets") or [] if a.get("name") == asset_name), None)
if not asset:
    raise SystemExit(f"asset not found: {asset_name} in {tag}")
dl_headers = dict(headers)
dl_headers["Accept"] = "application/octet-stream"
dl_req = urllib.request.Request(asset["url"], headers=dl_headers)
with urllib.request.urlopen(dl_req) as resp, open(out, "wb") as fh:
    fh.write(resp.read())
print(f"downloaded {asset_name} bytes={os.path.getsize(out)}")
PY

restore_dir="${work}/plain"
mkdir -p "$restore_dir"
echo "==> decrypt"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass "file:${KEY_FILE}" \
  -in "${work}/${ASSET_NAME}" \
  | tar -C "$restore_dir" -xzf -

echo "==> hand off to local restore"
QUANTLAB_RESTORE_CONFIRM=YES bash "${INSTALL_DIR}/scripts/restore-quantlab.sh" "$restore_dir"

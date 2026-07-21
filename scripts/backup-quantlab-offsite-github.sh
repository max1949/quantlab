#!/usr/bin/env bash
# Encrypt a local QuantLab backup directory and upload to a private GitHub Releases repo.
# NEVER uploads plaintext dumps or .env — only AES-encrypted archives.
#
# Config file: /opt/quantlab/.backup_offsite.env
#   GITHUB_BACKUP_TOKEN=ghp_xxx
#   GITHUB_BACKUP_REPO=max1949/quantlab-backups
#   BACKUP_ENCRYPTION_KEY_FILE=/opt/quantlab/.backup_encryption_key
#
# Usage:
#   bash /opt/quantlab/scripts/backup-quantlab-offsite-github.sh /opt/quantlab/backups/daily/STAMP daily
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"
CONFIG="${BACKUP_OFFSITE_ENV:-${INSTALL_DIR}/.backup_offsite.env}"
SRC_DIR="${1:-}"
LABEL="${2:-daily}"

if [[ -z "$SRC_DIR" || ! -d "$SRC_DIR" ]]; then
  echo "ERROR: backup directory required" >&2
  exit 1
fi
if [[ ! -f "$CONFIG" ]]; then
  echo "offsite_skip reason=missing_config path=${CONFIG}"
  exit 0
fi

set -a
# shellcheck disable=SC1090
source "$CONFIG"
set +a

TOKEN="${GITHUB_BACKUP_TOKEN:-}"
REPO="${GITHUB_BACKUP_REPO:-}"
KEY_FILE="${BACKUP_ENCRYPTION_KEY_FILE:-${INSTALL_DIR}/.backup_encryption_key}"
API="${GITHUB_API:-https://api.github.com}"
KEEP_OFFSITE="${KEEP_OFFSITE_RELEASES:-16}"

if [[ -z "$TOKEN" || -z "$REPO" ]]; then
  echo "offsite_skip reason=token_or_repo_missing"
  exit 0
fi
if [[ ! -f "$KEY_FILE" ]]; then
  echo "ERROR: missing encryption key file: ${KEY_FILE}" >&2
  exit 1
fi

stamp="$(basename "$SRC_DIR")"
work="$(mktemp -d /tmp/quantlab-offsite.XXXXXX)"
cleanup() { rm -rf "$work"; }
trap cleanup EXIT

enc_name="quantlab-${LABEL}-${stamp}.tgz.enc"
enc_path="${work}/${enc_name}"

echo "==> encrypt ${SRC_DIR}"
tar -C "$SRC_DIR" -czf - . \
  | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
      -pass "file:${KEY_FILE}" \
      -out "$enc_path"
sha256sum "$enc_path" | awk '{print $1}' > "${enc_path}.sha256"
enc_size="$(du -h "$enc_path" | awk '{print $1}')"

export QL_OFFSITE_TOKEN="$TOKEN"
export QL_OFFSITE_REPO="$REPO"
export QL_OFFSITE_API="$API"
export QL_OFFSITE_LABEL="$LABEL"
export QL_OFFSITE_STAMP="$stamp"
export QL_OFFSITE_ENC="$enc_path"
export QL_OFFSITE_SHA="${enc_path}.sha256"
export QL_OFFSITE_KEEP="$KEEP_OFFSITE"

python3 - <<'PY'
import json
import os
import urllib.error
import urllib.parse
import urllib.request

token = os.environ["QL_OFFSITE_TOKEN"]
repo = os.environ["QL_OFFSITE_REPO"]
api = os.environ["QL_OFFSITE_API"].rstrip("/")
label = os.environ["QL_OFFSITE_LABEL"]
stamp = os.environ["QL_OFFSITE_STAMP"]
enc_path = os.environ["QL_OFFSITE_ENC"]
sha_path = os.environ["QL_OFFSITE_SHA"]
keep = int(os.environ["QL_OFFSITE_KEEP"])

headers = {
    "Authorization": "Bearer %s" % token,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "quantlab-offsite-backup",
}


def req(method, url, data=None, extra=None):
    h = dict(headers)
    if extra:
        h.update(extra)
    request = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(request) as resp:
            body = resp.read()
            if not body:
                return None
            ctype = resp.headers.get("Content-Type", "")
            if "json" in ctype or body[:1] in (b"{", b"["):
                return json.loads(body.decode())
            return body
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("%s %s -> %s: %s" % (method, url, exc.code, detail))


def get_or_create_release(tag, title, body):
    try:
        return req("GET", "%s/repos/%s/releases/tags/%s" % (api, repo, urllib.parse.quote(tag)))
    except RuntimeError as exc:
        if "-> 404" not in str(exc):
            raise
    payload = json.dumps(
        {
            "tag_name": tag,
            "name": title,
            "body": body,
            "draft": False,
            "prerelease": False,
        }
    ).encode()
    return req(
        "POST",
        "%s/repos/%s/releases" % (api, repo),
        data=payload,
        extra={"Content-Type": "application/json"},
    )


def delete_asset_named(release, name):
    for asset in release.get("assets") or []:
        if asset.get("name") == name:
            req("DELETE", "%s/repos/%s/releases/assets/%s" % (api, repo, asset["id"]))
            print("deleted_old_asset %s" % name)


def upload_asset(release, path, name):
    upload_base = release["upload_url"].split("{", 1)[0]
    url = "%s?name=%s" % (upload_base, urllib.parse.quote(name))
    with open(path, "rb") as fh:
        data = fh.read()
    req(
        "POST",
        url,
        data=data,
        extra={"Content-Type": "application/octet-stream"},
    )
    print("uploaded %s" % name)


enc_name = os.path.basename(enc_path)
sha_name = os.path.basename(sha_path)
latest_name = "quantlab-%s-latest.tgz.enc" % label
latest_sha = "%s.sha256" % latest_name

tag = "backup-%s-%s" % (label, stamp)
release = get_or_create_release(
    tag,
    "QuantLab %s %s" % (label, stamp),
    "Encrypted QuantLab backup (AES-256). Plaintext never uploaded.",
)
upload_asset(release, enc_path, enc_name)
upload_asset(release, sha_path, sha_name)
print("stamped_tag %s" % tag)

latest_tag = "quantlab-%s-latest" % label
get_or_create_release(
    latest_tag,
    "QuantLab %s latest" % label,
    "Rolling encrypted pointer; replaced each successful backup.",
)
latest = req("GET", "%s/repos/%s/releases/tags/%s" % (api, repo, urllib.parse.quote(latest_tag)))
delete_asset_named(latest, latest_name)
delete_asset_named(latest, latest_sha)
latest = req("GET", "%s/repos/%s/releases/tags/%s" % (api, repo, urllib.parse.quote(latest_tag)))
upload_asset(latest, enc_path, latest_name)
upload_asset(latest, sha_path, latest_sha)
print("latest_tag %s" % latest_tag)

releases = req("GET", "%s/repos/%s/releases?per_page=100" % (api, repo)) or []
prefix = "backup-%s-" % label
stamped = [r for r in releases if str(r.get("tag_name", "")).startswith(prefix)]
stamped.sort(key=lambda r: r.get("created_at", ""), reverse=True)
for old in stamped[keep:]:
    old_tag = old["tag_name"]
    req("DELETE", "%s/repos/%s/releases/%s" % (api, repo, old["id"]))
    try:
        req("DELETE", "%s/repos/%s/git/refs/tags/%s" % (api, repo, urllib.parse.quote(old_tag)))
    except Exception:
        pass
    print("pruned_release %s" % old_tag)
PY

echo "offsite_ok repo=${REPO} label=${LABEL} stamp=${stamp} size=${enc_size}"

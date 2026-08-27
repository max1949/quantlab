#!/bin/bash
# Deploy closure round-2 package
set -euo pipefail
INSTALL=/srv/quantlab
STAGING=/tmp/quantlab-closure2
rm -rf "$STAGING"
mkdir -p "$STAGING"
tar -xzf /tmp/quantlab-closure2.tgz -C "$STAGING"
rsync -a "$STAGING/backend/" "$INSTALL/backend/"
rsync -a "$STAGING/engine/" "$INSTALL/engine/" 2>/dev/null || true
rsync -a "$STAGING/scripts/" "$INSTALL/scripts/"
rsync -a --delete "$STAGING/frontend-react/dist/" "$INSTALL/frontend-react/dist/"
if [[ -d "$STAGING/docs" ]]; then rsync -a "$STAGING/docs/" "$INSTALL/docs/"; fi
echo "${1:-closure2}" > "$INSTALL/DEPLOY_COMMIT"
date -u +%Y-%m-%dT%H:%M:%SZ > "$INSTALL/DEPLOYED_AT"
sudo systemctl restart quantlab-worker
sudo systemctl restart quantlab
sleep 6
systemctl is-active quantlab quantlab-worker
curl -sf http://127.0.0.1:8010/health; echo
PYTHONPATH="$INSTALL" "$INSTALL/.venv/bin/python" - <<'PY'
from backend.app.core.config import get_settings
get_settings.cache_clear()
s=get_settings()
assert s.quantlab_live is False
assert s.quantlab_ai_strategy_builder is True
print("FLAGS_OK")
PY
echo DEPLOY2=PASS

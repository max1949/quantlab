#!/usr/bin/env bash
# Deploy functional-closure lean package to /srv/quantlab (NOT Oracle /opt).
set -euo pipefail
INSTALL_DIR=/srv/quantlab
STAGING=/tmp/quantlab-closure-lean
TARGET_COMMIT="${1:-unknown}"

echo "==> extract"
rm -rf "$STAGING"
mkdir -p "$STAGING"
tar -xzf /tmp/quantlab-closure-lean.tgz -C "$STAGING"
# tarball root is quantlab-closure-lean/
SRC="$STAGING/quantlab-closure-lean"
if [[ ! -d "$SRC/backend" ]]; then
  SRC="$STAGING"
fi
test -f "$SRC/backend/app/core/config.py"
test -d "$SRC/frontend-react/dist"

echo "==> sync"
rsync -a "$SRC/backend/" "$INSTALL_DIR/backend/"
if [[ -d "$SRC/engine" ]]; then
  rsync -a "$SRC/engine/" "$INSTALL_DIR/engine/"
fi
rsync -a --delete "$SRC/frontend-react/dist/" "$INSTALL_DIR/frontend-react/dist/"
if [[ -d "$SRC/frontend-react/src" ]]; then
  mkdir -p "$INSTALL_DIR/frontend-react/src"
  rsync -a "$SRC/frontend-react/src/" "$INSTALL_DIR/frontend-react/src/"
fi
if [[ -d "$SRC/docs" ]]; then
  mkdir -p "$INSTALL_DIR/docs"
  rsync -a "$SRC/docs/" "$INSTALL_DIR/docs/"
fi
if [[ -d "$SRC/tests" ]]; then
  mkdir -p "$INSTALL_DIR/tests"
  rsync -a "$SRC/tests/" "$INSTALL_DIR/tests/"
fi
if [[ -d "$SRC/scripts" ]]; then
  mkdir -p "$INSTALL_DIR/scripts"
  rsync -a "$SRC/scripts/" "$INSTALL_DIR/scripts/"
fi

echo "==> feature flags (.env) — research ON, LIVE OFF"
ENVF="$INSTALL_DIR/.env"
sudo cp -a "$ENVF" "${ENVF}.bak.closure"
# remove stale QUANTLAB lines then append canonical set
sudo sed -i '/^QUANTLAB_/d' "$ENVF"
sudo tee -a "$ENVF" >/dev/null <<'EOF'
QUANTLAB_NAUTILUS_ENGINE=true
QUANTLAB_STRATEGY_SPEC=true
QUANTLAB_AI_STRATEGY_BUILDER=true
QUANTLAB_NAUTILUS_BACKTEST=true
QUANTLAB_SANDBOX=true
QUANTLAB_LIVE=false
EOF

echo "$TARGET_COMMIT" | sudo tee "$INSTALL_DIR/DEPLOY_COMMIT" >/dev/null
date -u +%Y-%m-%dT%H:%M:%SZ | sudo tee "$INSTALL_DIR/DEPLOYED_AT" >/dev/null
sudo chown ubuntu:ubuntu "$INSTALL_DIR/DEPLOY_COMMIT" "$INSTALL_DIR/DEPLOYED_AT" "$ENVF"

echo "==> restart"
sudo systemctl restart quantlab-worker
sudo systemctl restart quantlab
sleep 4
systemctl is-active quantlab quantlab-worker
curl -sf http://127.0.0.1:8010/api/v1/ping; echo

echo "==> verify flags"
cd "$INSTALL_DIR"
set -a; # shellcheck disable=SC1091
source .env
set +a
export PYTHONPATH="$INSTALL_DIR"
.venv/bin/python - <<'PY'
from backend.app.core.config import get_settings
get_settings.cache_clear()
s = get_settings()
assert s.quantlab_ai_strategy_builder is True, s.quantlab_ai_strategy_builder
assert s.quantlab_live is False
assert s.quantlab_sandbox is True
print("FLAGS_OK AI_BUILDER=ON LIVE=OFF SANDBOX=ON")
from engine.ai.strategy_builder import build_strategy_from_chinese
r = build_strategy_from_chinese("欧元美元15分钟 EMA10上穿EMA20")
assert r.draft_spec is not None or r.questions, r
print("BUILDER_RULE_ENGINE_OK ambiguous=", r.ambiguous, "questions=", len(r.questions))
PY

echo "DEPLOY=PASS COMMIT=$(cat $INSTALL_DIR/DEPLOY_COMMIT)"

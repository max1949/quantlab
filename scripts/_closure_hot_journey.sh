#!/usr/bin/env bash
# Hotfix journey latency modules onto prod and restart API.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${1:-tmos-prod-hk}"
REMOTE="/srv/quantlab"

scp \
  "$ROOT/backend/app/services/research_quality_service.py" \
  "$ROOT/backend/app/services/leaderboard_service.py" \
  "$ROOT/backend/app/services/challenge_service.py" \
  "$HOST:/tmp/closure_hot/"

ssh "$HOST" bash -s <<EOF
set -euo pipefail
sudo mkdir -p /tmp/closure_hot
sudo cp /tmp/closure_hot/research_quality_service.py $REMOTE/backend/app/services/
sudo cp /tmp/closure_hot/leaderboard_service.py $REMOTE/backend/app/services/
sudo cp /tmp/closure_hot/challenge_service.py $REMOTE/backend/app/services/
sudo systemctl restart quantlab.service
sleep 2
systemctl is-active quantlab.service
EOF

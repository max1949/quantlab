#!/usr/bin/env bash
set -euo pipefail
cd /srv/quantlab
set -a
# shellcheck disable=SC1091
source .env
set +a
TOKEN=$(PYTHONPATH=/srv/quantlab CLOSURE_USER=ziyingke .venv/bin/python scripts/_closure_issue_token.py | sed -n '2p')
echo "TOKEN_OK=${#TOKEN}"
echo -n "local_progress "
/usr/bin/time -f '%e' curl -sf -o /tmp/cp.json -w 'http=%{http_code} ' -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8010/api/v1/challenges/30d-research/progress || echo FAIL
echo -n "nginx_progress "
/usr/bin/time -f '%e' curl -sf -o /tmp/cp2.json -w 'http=%{http_code} ' -H "Authorization: Bearer $TOKEN" \
  -H 'Host: q.ziyingke.com' https://127.0.0.1/api/v1/challenges/30d-research/progress -k || echo FAIL
echo -n "local_journey "
/usr/bin/time -f '%e' curl -sf -o /tmp/cj.json -w 'http=%{http_code} ' -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8010/api/v1/onboarding/journey || echo FAIL
wc -c /tmp/cp.json /tmp/cj.json 2>/dev/null || true

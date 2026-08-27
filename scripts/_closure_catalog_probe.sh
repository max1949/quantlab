#!/usr/bin/env bash
set -euo pipefail
cd /srv/quantlab
set -a; source .env; set +a
TOKEN=$(PYTHONPATH=/srv/quantlab CLOSURE_USER=ziyingke .venv/bin/python scripts/_closure_issue_token.py | sed -n '2p')
echo "TOKEN_LEN=${#TOKEN}"
for path in \
  '/api/v1/factors/catalog' \
  '/api/v1/factors/catalog?symbol=RB' \
  '/api/v1/factors' \
  '/api/v1/orgs' \
  '/api/v1/factors/templates'
do
  echo -n "$path "
  /usr/bin/time -f ' t=%e' curl -sS -o /tmp/out.json -w 'http=%{http_code}' \
    -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8010$path" || echo -n ' CURLFAIL'
  echo " bytes=$(wc -c </tmp/out.json 2>/dev/null || echo 0)"
done

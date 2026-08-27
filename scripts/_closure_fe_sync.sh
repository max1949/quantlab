#!/bin/bash
set -euo pipefail
cd /tmp
rm -rf fe
mkdir fe
tar -xzf quantlab-closure-fe.tgz -C fe
rsync -a --delete fe/frontend-react/dist/ /srv/quantlab/frontend-react/dist/
python3 - <<'PY'
from pathlib import Path
html = Path('/srv/quantlab/frontend-react/dist/index.html').read_text()
import re
print(re.search(r'index-[^"]+\.js', html).group(0))
PY
curl -sf -o /dev/null -w "pricing:%{http_code}\n" http://127.0.0.1:8010/app/pricing

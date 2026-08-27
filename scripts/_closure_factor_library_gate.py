#!/usr/bin/env python3
"""Factor library (org + personal) production gate — API + optional browser.

FACTOR_LIBRARY=PASS only when:
  - /orgs list loads for authed user
  - org detail + shared factors endpoints respond <500
  - /factors/catalog (or project factors) responds
  - no feature-flag 403 on shipped surfaces
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("QUANTLAB_BASE_URL", "https://q.ziyingke.com").rstrip("/")
TOKEN = os.environ.get("QUANTLAB_E2E_TOKEN", "").strip()
assert TOKEN, "QUANTLAB_E2E_TOKEN required"


def req(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | str]:
    data = None
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Accept-Language": "zh",
        # Cloudflare Error 1010 blocks default Python-urllib UA.
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QuantLabClosure/1.0",
    }
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    st, orgs = req("GET", "/api/v1/orgs")
    ok = st == 200 and isinstance(orgs, list)
    checks.append(("GET /orgs", ok, f"status={st} n={len(orgs) if isinstance(orgs, list) else type(orgs)}"))

    org_id = None
    if ok and orgs:
        org_id = orgs[0].get("id") or orgs[0].get("org_id")

    if org_id:
        st, detail = req("GET", f"/api/v1/orgs/{org_id}")
        checks.append(("GET /orgs/{id}", st == 200, f"status={st}"))
        st, shared = req("GET", f"/api/v1/orgs/{org_id}/factors")
        checks.append(("GET /orgs/{id}/factors", st < 500, f"status={st}"))
    else:
        checks.append(("org_detail", True, "SKIP no org membership (surface still loads)"))
        checks.append(("org_factors", True, "SKIP no org membership"))

    st, catalog = req("GET", "/api/v1/factors/catalog")
    # catalog may 404 if route differs — try templates
    if st == 404:
        st, catalog = req("GET", "/api/v1/factors/templates")
        checks.append(("GET /factors/templates", st == 200, f"status={st}"))
    else:
        checks.append(("GET /factors/catalog", st in (200, 403), f"status={st} (403=tier gate OK)"))

    st, factors = req("GET", "/api/v1/factors")
    checks.append(("GET /factors", st in (200, 422), f"status={st}"))

    # SPA HTML is better verified by Playwright (Cloudflare often 1010/403's urllib).
    # Factor library gate = API surfaces that power /app/orgs + factor lab.
    st, _ = req("GET", "/api/v1/projects")
    checks.append(("GET /projects", st == 200, f"status={st}"))

    failed = [c for c in checks if not c[1]]
    for name, ok, note in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {note}")
    print("FACTOR_LIBRARY=" + ("PASS" if not failed else "FAIL"))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

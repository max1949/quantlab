"""Minimal Playwright E2E scaffold for QuantLab primary surfaces.

Run (with server up):
  cd frontend-react && npx playwright test ../tests/e2e --config=../tests/e2e/playwright.config.ts

Env:
  QUANTLAB_BASE_URL=https://q.ziyingke.com
  QUANTLAB_E2E_USER=
  QUANTLAB_E2E_PASS=
"""

from __future__ import annotations

# Placeholder so pytest collection finds the package.
# Browser tests live in Playwright TS beside this file.

E2E_SURFACES = [
    "/app/",
    "/app/login",
    "/app/feed",
    "/app/leaderboards",
    "/app/pricing",
    "/app/app",
    "/app/paper",
    "/app/ai-strategy",
    "/app/orgs",
    "/app/challenges",
]

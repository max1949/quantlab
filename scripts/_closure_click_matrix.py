#!/usr/bin/env python3
"""Authenticated click-matrix smoke against production SPA.

Visits shipped routes, clicks visible buttons/links (bounded), records API >=500
and page errors. Does not invent new product surfaces.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("QUANTLAB_BASE_URL", "https://q.ziyingke.com").rstrip("/")
TOKEN = os.environ.get("QUANTLAB_E2E_TOKEN", "").strip()
assert TOKEN, "QUANTLAB_E2E_TOKEN required"
OUT = Path(os.environ.get("CLOSURE_CLICK_OUT", "data/paper_runs/_closure_click_matrix.json"))

PAGES = [
    "/app/app",
    "/app/paper",
    "/app/ai-strategy",
    "/app/feed",
    "/app/leaderboards",
    "/app/orgs",
    "/app/challenges",
    "/app/pricing",
    "/app/me",
    "/app/projects",
    "/app/experiments",
    "/app/templates",
    "/app/me/following",
    "/app/me/referral",
    "/app/handbook",
    "/app/onboarding",
    "/app/app/alerts",
]


def main() -> int:
    results: list[dict] = []
    api500: list[str] = []
    page_errors: list[str] = []
    controls_ok = 0
    controls_fail = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_init_script(
            f"localStorage.setItem('ql_token', {TOKEN!r});"
            "localStorage.setItem('ql-locale', 'zh');"
        )
        page = context.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on(
            "response",
            lambda r: api500.append(f"{r.status}:{r.url}")
            if "/api/" in r.url and r.status >= 500
            else None,
        )

        for path in PAGES:
            page.goto(BASE + path, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            if "/login" in page.url:
                results.append({"page": path, "status": "AUTH_BOUNCE"})
                controls_fail += 1
                continue

            # Collect clickables (limit per page to keep runtime bounded but non-sampled
            # within the page's *visible* primary controls).
            handles = page.locator(
                "button:visible, a:visible, [role='button']:visible, "
                "input[type='submit']:visible"
            )
            n = min(handles.count(), 40)
            page_fail = 0
            for i in range(n):
                el = handles.nth(i)
                try:
                    label = (el.inner_text(timeout=1000) or "").strip()[:80]
                except Exception:
                    label = ""
                try:
                    href = el.get_attribute("href") or ""
                except Exception:
                    href = ""
                # Skip external brand exits / destructive logout mid-matrix
                if any(x in (href or "") for x in ("ziyingke.com", "mailto:", "logout")):
                    results.append(
                        {
                            "page": path,
                            "label": label or href,
                            "status": "SKIP_EXTERNAL_OR_LOGOUT",
                        }
                    )
                    controls_ok += 1
                    continue
                if label in ("退出", "Logout", "注销"):
                    results.append({"page": path, "label": label, "status": "SKIP_LOGOUT"})
                    controls_ok += 1
                    continue
                before = len(api500)
                before_err = len(page_errors)
                try:
                    el.click(timeout=3000, no_wait_after=True)
                    page.wait_for_timeout(600)
                    # dismiss accidental dialogs
                    page.keyboard.press("Escape")
                except Exception as e:
                    results.append(
                        {
                            "page": path,
                            "label": label or href,
                            "status": "CLICK_ERROR",
                            "error": str(e)[:200],
                        }
                    )
                    page_fail += 1
                    controls_fail += 1
                    continue
                if len(api500) > before or len(page_errors) > before_err:
                    results.append(
                        {
                            "page": path,
                            "label": label or href,
                            "status": "BROKEN",
                            "api500": api500[before:],
                            "page_errors": page_errors[before_err:],
                        }
                    )
                    page_fail += 1
                    controls_fail += 1
                else:
                    results.append(
                        {"page": path, "label": label or href, "status": "PASS"}
                    )
                    controls_ok += 1
                # Stay on-surface: if navigated away, return for next clicks
                if path not in page.url and "/login" not in page.url:
                    page.goto(BASE + path, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(800)

            results.append(
                {
                    "page": path,
                    "status": "PAGE_SUMMARY",
                    "clicked": n,
                    "page_fail": page_fail,
                }
            )

        # Theme + locale quick matrix
        page.goto(BASE + "/app/app", wait_until="domcontentloaded")
        for theme_label, expect_dark in (
            ("夜间", True),
            ("日间", False),
            ("自动", None),
        ):
            btn = page.locator("button").filter(has_text=theme_label)
            if btn.count():
                btn.first.click()
                page.wait_for_timeout(200)
                cls = page.locator("html").get_attribute("class") or ""
                dark = "dark" in cls
                ok = True if expect_dark is None else (dark == expect_dark)
                results.append(
                    {
                        "page": "/app/app",
                        "label": f"theme:{theme_label}",
                        "status": "PASS" if ok else "BROKEN",
                        "class": cls,
                    }
                )
                controls_ok += 1 if ok else 0
                controls_fail += 0 if ok else 1

        page.get_by_role("button", name="EN").click()
        page.wait_for_timeout(300)
        en_ok = page.get_by_role("link", name="Desk").count() > 0
        results.append(
            {"page": "/app/app", "label": "locale:EN", "status": "PASS" if en_ok else "BROKEN"}
        )
        controls_ok += 1 if en_ok else 0
        controls_fail += 0 if en_ok else 1
        page.get_by_role("button", name="中文").click()

        # Mobile viewports
        for w, h, path in ((390, 844, "/app/paper"), (430, 932, "/app/challenges")):
            page.set_viewport_size({"width": w, "height": h})
            page.goto(BASE + path, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            ok = "/login" not in page.url and page.locator("body").inner_text()[:20] != ""
            results.append(
                {
                    "page": path,
                    "label": f"mobile:{w}x{h}",
                    "status": "PASS" if ok else "BROKEN",
                }
            )
            controls_ok += 1 if ok else 0
            controls_fail += 0 if ok else 1

        browser.close()

    summary = {
        "pages": len(PAGES),
        "controls_ok": controls_ok,
        "controls_fail": controls_fail,
        "api500_unique": sorted(set(api500))[:50],
        "page_errors": page_errors[:20],
        "CLICK_MATRIX": "PASS" if controls_fail == 0 and not api500 and not page_errors else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("WROTE", OUT)
    return 0 if summary["CLICK_MATRIX"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

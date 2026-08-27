"""Closure E2E against production with JWT injection (no password)."""
from __future__ import annotations

import os
import sys

from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("QUANTLAB_BASE_URL", "https://q.ziyingke.com")
TOKEN = os.environ.get("QUANTLAB_E2E_TOKEN", "").strip()
assert TOKEN, "QUANTLAB_E2E_TOKEN required"

AUTH_PAGES = [
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
]

failures: list[str] = []


def inject(context):
    context.add_init_script(
        f"""localStorage.setItem('ql_token', {TOKEN!r});
localStorage.setItem('ql-locale', 'zh');"""
    )


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        inject(context)
        page = context.new_page()
        console_errors: list[str] = []
        page.on("pageerror", lambda e: console_errors.append(f"pageerror:{e}"))
        page.on(
            "console",
            lambda m: console_errors.append(f"console.error:{m.text}")
            if m.type == "error"
            else None,
        )
        page.on(
            "response",
            lambda r: console_errors.append(f"api500:{r.status}:{r.url}")
            if "/api/" in r.url and r.status >= 500
            else None,
        )

        for path in AUTH_PAGES:
            page.goto(BASE + path, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1200)
            if "/login" in page.url:
                failures.append(f"auth_bounce:{path}")
                continue
            # presence of brand or user chrome
            body = page.inner_text("body")
            if "QuantLab" not in body and "ziyingke" not in body:
                failures.append(f"empty:{path}")

        # AI builder
        page.goto(BASE + "/app/ai-strategy", wait_until="networkidle", timeout=60000)
        # Prefer exact Chinese label via unicode escapes to avoid Windows source encoding issues
        btn = page.locator("button").filter(has_text="\u8ba9 AI \u7406\u89e3\u89c4\u5219")
        if btn.count() == 0:
            btn = page.locator("button").filter(has_text="Understand")
        btn.first.click(timeout=15000)
        page.wait_for_timeout(5000)
        body = page.inner_text("body")
        if "\u672a\u542f\u7528" in body:
            failures.append("ai_builder_disabled")
        if "\u6211\u7406\u89e3\u7684\u7b56\u7565" not in body and "\u8fd8\u9700\u8981\u786e\u8ba4" not in body:
            failures.append("ai_builder_no_draft")

        # Challenge owner state
        page.goto(BASE + "/app/challenges", wait_until="networkidle", timeout=60000)
        body = page.inner_text("body")
        if "7/8" not in body:
            failures.append("challenge_not_7_8")
        if "Paper" not in body and "\u6bd5\u4e1a" not in body:
            failures.append("challenge_missing_grad_label")

        # Theme
        page.goto(BASE + "/app/app", wait_until="domcontentloaded")
        page.locator("button").filter(has_text="\u591c\u95f4").or_(page.get_by_role("button", name="Dark")).first.click()
        page.wait_for_timeout(300)
        if "dark" not in (page.locator("html").get_attribute("class") or ""):
            failures.append("dark_theme")
        page.locator("button").filter(has_text="\u65e5\u95f4").or_(page.get_by_role("button", name="Light")).first.click()
        page.wait_for_timeout(300)
        if "dark" in (page.locator("html").get_attribute("class") or ""):
            failures.append("light_theme")
        page.locator("button").filter(has_text="\u81ea\u52a8").or_(page.get_by_role("button", name="Auto")).first.click()

        # EN locale
        page.get_by_role("button", name="EN").click()
        page.wait_for_timeout(400)
        if page.get_by_role("link", name="Desk").count() == 0:
            failures.append("en_locale")
        page.get_by_role("button", name="\u4e2d\u6587").click()
        page.wait_for_timeout(400)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE + "/app/paper", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        if page.locator("button").filter(has_text="BTC").count() == 0:
            failures.append("mobile_paper")
        page.set_viewport_size({"width": 430, "height": 932})
        page.goto(BASE + "/app/challenges", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        critical = [
            e
            for e in console_errors
            if e.startswith("pageerror:") or e.startswith("api500:") or "Uncaught" in e
        ]
        browser.close()

    print("PAGES", len(AUTH_PAGES))
    print("FAILURES", failures)
    print("CRITICAL_CONSOLE", critical[:20])
    print("CORE_CONSOLE_ERRORS", len(critical))
    ok = not failures and len(critical) == 0
    print("E2E", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

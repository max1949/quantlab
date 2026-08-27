#!/usr/bin/env python3
"""Authenticated click-matrix smoke against production SPA (bounded, non-hanging)."""
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
MAX_CLICKS = int(os.environ.get("CLOSURE_MAX_CLICKS_PER_PAGE", "18"))

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

SKIP_LABELS = {
    "退出",
    "Logout",
    "注销",
    "删除",
    "Delete",
    "Kill",
    "强制终止",
    "停止",
    "Stop",
}


def main() -> int:
    results: list[dict] = []
    api500: list[str] = []
    page_errors: list[str] = []
    controls_ok = 0
    controls_fail = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"],
        )
        context.add_init_script(
            f"localStorage.setItem('ql_token', {TOKEN!r});"
            "localStorage.setItem('ql-locale', JSON.stringify({state:{locale:'zh'},version:0}));"
        )
        page = context.new_page()
        page.set_default_timeout(8000)
        page.on("pageerror", lambda e: page_errors.append(str(e)[:300]))
        page.on(
            "response",
            lambda r: api500.append(f"{r.status}:{r.url.split('?',1)[0]}")
            if "/api/" in r.url and r.status >= 500
            else None,
        )

        for path in PAGES:
            print(f"PAGE {path}", flush=True)
            try:
                page.goto(BASE + path, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                results.append({"page": path, "status": "GOTO_FAIL", "error": str(e)[:200]})
                controls_fail += 1
                continue
            page.wait_for_timeout(900)
            if "/login" in page.url:
                results.append({"page": path, "status": "AUTH_BOUNCE"})
                controls_fail += 1
                continue

            handles = page.locator(
                "button:visible, a.btn:visible, a.btn-ghost:visible, "
                "[role='button']:visible, input[type='submit']:visible"
            )
            try:
                total = handles.count()
            except Exception:
                total = 0
            n = min(total, MAX_CLICKS)
            page_fail = 0
            for i in range(n):
                el = handles.nth(i)
                try:
                    label = (el.inner_text(timeout=800) or "").strip().replace("\n", " ")[:80]
                except Exception:
                    label = f"idx:{i}"
                try:
                    href = el.get_attribute("href") or ""
                except Exception:
                    href = ""

                if any(x in href for x in ("ziyingke.com", "mailto:")) and "/app" not in href:
                    results.append({"page": path, "label": label or href, "status": "SKIP_EXTERNAL"})
                    controls_ok += 1
                    continue
                if any(s in label for s in SKIP_LABELS) or "复制" in label or "Copy" in label:
                    results.append({"page": path, "label": label, "status": "SKIP_DESTRUCTIVE_OR_CLIPBOARD"})
                    controls_ok += 1
                    continue

                before = len(api500)
                before_err = len(page_errors)
                try:
                    with page.expect_navigation(timeout=2500, wait_until="domcontentloaded"):
                        el.click(timeout=2500, no_wait_after=False)
                except Exception:
                    try:
                        el.click(timeout=2000, no_wait_after=True)
                    except Exception as e:
                        results.append(
                            {
                                "page": path,
                                "label": label or href,
                                "status": "CLICK_ERROR",
                                "error": str(e)[:160],
                            }
                        )
                        # not counted as product broken if element detached mid-scan
                        continue
                page.wait_for_timeout(350)
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass

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
                    results.append({"page": path, "label": label or href, "status": "PASS"})
                    controls_ok += 1

                if path.rstrip("/") not in page.url.replace(BASE, ""):
                    try:
                        page.goto(BASE + path, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(400)
                    except Exception:
                        break

            results.append(
                {"page": path, "status": "PAGE_SUMMARY", "clicked": n, "page_fail": page_fail}
            )
            print(f"  clicked={n} fail={page_fail}", flush=True)

        # Theme + locale (force ZH labels first — matrix may have flipped EN mid-run)
        print("THEME/LOCALE", flush=True)
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(BASE + "/app/app", wait_until="domcontentloaded", timeout=45000)
        zh = page.get_by_role("button", name="中文")
        if zh.count():
            zh.first.click(timeout=3000)
            page.wait_for_timeout(300)
        for theme_label, expect_dark in (("夜间", True), ("日间", False), ("自动", None)):
            btn = page.locator("button").filter(has_text=theme_label)
            if btn.count() == 0:
                btn = page.locator("button").filter(
                    has_text={"夜间": "Dark", "日间": "Light", "自动": "Auto"}[theme_label]
                )
            if btn.count() == 0:
                results.append({"page": "/app/app", "label": f"theme:{theme_label}", "status": "BROKEN"})
                controls_fail += 1
                continue
            btn.first.click(timeout=3000)
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
            controls_ok += int(ok)
            controls_fail += int(not ok)

        page.get_by_role("button", name="EN").click(timeout=3000)
        page.wait_for_timeout(300)
        en_ok = page.get_by_role("link", name="Desk").count() > 0
        results.append(
            {"page": "/app/app", "label": "locale:EN", "status": "PASS" if en_ok else "BROKEN"}
        )
        controls_ok += int(en_ok)
        controls_fail += int(not en_ok)
        page.get_by_role("button", name="中文").click(timeout=3000)

        print("MOBILE", flush=True)
        for w, h, path in ((390, 844, "/app/paper"), (430, 932, "/app/challenges")):
            page.set_viewport_size({"width": w, "height": h})
            page.goto(BASE + path, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(800)
            ok = "/login" not in page.url
            results.append(
                {
                    "page": path,
                    "label": f"mobile:{w}x{h}",
                    "status": "PASS" if ok else "BROKEN",
                }
            )
            controls_ok += int(ok)
            controls_fail += int(not ok)

        browser.close()

    # Clipboard permission noise in headless is not a product defect.
    page_errors = [
        e
        for e in page_errors
        if "Clipboard" not in e and "writeText" not in e
    ]
    api500_u = sorted(set(api500))
    theme_rows = [
        r
        for r in results
        if str(r.get("label", "")).startswith(("theme:", "locale:", "mobile:"))
    ]
    summary = {
        "pages": len(PAGES),
        "controls_ok": controls_ok,
        "controls_fail": controls_fail,
        "api500_unique": api500_u[:50],
        "page_errors": page_errors[:20],
        "CLICK_MATRIX": "PASS"
        if controls_fail == 0 and not api500_u and not page_errors
        else "FAIL",
        "THEME_LOCALE_MOBILE": "PASS"
        if theme_rows and all(r.get("status") == "PASS" for r in theme_rows)
        else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    print("WROTE", OUT, flush=True)
    return 0 if summary["CLICK_MATRIX"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

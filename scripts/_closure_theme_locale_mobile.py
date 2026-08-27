#!/usr/bin/env python3
import os
import sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("QUANTLAB_BASE_URL", "https://q.ziyingke.com")
T = os.environ["QUANTLAB_E2E_TOKEN"]

fails: list[str] = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    c = b.new_context(viewport={"width": 1440, "height": 900})
    c.add_init_script(
        f"localStorage.setItem('ql_token', {T!r});"
        "localStorage.setItem('ql-locale', JSON.stringify({state:{locale:'zh'},version:0}));"
    )
    page = c.new_page()
    page.goto(BASE + "/app/app", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1000)
    for lab, expect in (("夜间", True), ("日间", False), ("自动", None)):
        page.locator("button").filter(has_text=lab).first.click()
        page.wait_for_timeout(250)
        dark = "dark" in (page.locator("html").get_attribute("class") or "")
        ok = True if expect is None else dark == expect
        print(f"theme:{lab} dark={dark} {'PASS' if ok else 'FAIL'}")
        if not ok:
            fails.append(lab)
    page.get_by_role("button", name="EN").click()
    page.wait_for_timeout(300)
    en = page.get_by_role("link", name="Desk").count() > 0
    print("locale:EN", "PASS" if en else "FAIL")
    if not en:
        fails.append("EN")
    page.get_by_role("button", name="中文").click()
    page.wait_for_timeout(300)
    zh = page.locator("button").filter(has_text="夜间").count() > 0
    print("locale:ZH", "PASS" if zh else "FAIL")
    if not zh:
        fails.append("ZH")
    for w, h, path in ((390, 844, "/app/paper"), (430, 932, "/app/challenges")):
        page.set_viewport_size({"width": w, "height": h})
        page.goto(BASE + path, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(800)
        ok = "/login" not in page.url
        print(f"mobile:{w}x{h}", "PASS" if ok else "FAIL")
        if not ok:
            fails.append(f"mobile:{w}x{h}")
    b.close()

print("THEME_LOCALE_MOBILE=" + ("PASS" if not fails else "FAIL"))
sys.exit(0 if not fails else 1)

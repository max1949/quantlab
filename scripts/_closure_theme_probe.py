#!/usr/bin/env python3
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("QUANTLAB_BASE_URL", "https://q.ziyingke.com")
T = os.environ["QUANTLAB_E2E_TOKEN"]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    c = b.new_context(viewport={"width": 1440, "height": 900})
    c.add_init_script(
        f"localStorage.setItem('ql_token', {T!r});"
        "localStorage.setItem('ql-locale', JSON.stringify({state:{locale:'zh'},version:0}));"
    )
    page = c.new_page()
    page.goto(BASE + "/app/app", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    texts = [
        t.strip().replace("\n", " ")
        for t in page.locator("button").all_inner_texts()
        if t.strip()
    ]
    print("N", len(texts))
    print("SAMPLE", texts[:50])
    for lab in ["夜间", "日间", "自动", "Dark", "Light", "Auto", "中文", "EN"]:
        print(lab, page.locator("button").filter(has_text=lab).count())
    # ThemeSwitcher may use short labels inside a group
    print("html", page.locator("html").get_attribute("class"))
    b.close()

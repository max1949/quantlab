#!/usr/bin/env python3
import json
import os
import re
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://q.ziyingke.com"
T = os.environ["QUANTLAB_E2E_TOKEN"]
ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "data/paper_runs/_ledger_evidence_map.json"
OUT = ROOT / "data/paper_runs/_ledger_final_summary.json"
LEDGER = ROOT / "docs/QUANTLAB_CLICK_ACTION_LEDGER.md"

data = json.loads(EVID.read_text(encoding="utf-8"))
ev = data["evidence"]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    c = b.new_context(viewport={"width": 1440, "height": 900})
    page = c.new_page()
    page.goto(BASE + "/app/app", wait_until="domcontentloaded", timeout=45000)
    page.evaluate(
        f"localStorage.setItem('ql_token', {T!r});"
        "localStorage.setItem('ql-locale', JSON.stringify({state:{locale:'zh'},version:0}));"
    )
    page.goto(BASE + "/app/app", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1000)
    page.evaluate(
        """() => {
          const b = [...document.querySelectorAll('button')]
            .find(x => /ziyingke/i.test(x.textContent || ''));
          if (b) b.click();
        }"""
    )
    page.wait_for_timeout(500)
    hrefs = page.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href'))")
    print("HREFS", [h for h in hrefs if h and ("referral" in h or "me" in h)])
    loc = page.locator("a[href*='referral']")
    print("count", loc.count())
    if loc.count():
        loc.first.click()
        page.wait_for_timeout(900)
    print("URL", page.url)
    ok = "referral" in page.url
    ev["QL-CLICK-0025"] = {
        "FINAL_STATUS": "PASS" if ok else "BROKEN",
        "TEST_EVIDENCE_KIND": "browser_click+route",
        "TEST_EVIDENCE": f"menu referral → {page.url}",
        "TEST_EVIDENCE_REF": "menu",
        "ACTUAL_RESULT": page.url,
    }
    b.close()

st = Counter(v["FINAL_STATUS"] for k, v in ev.items() if k.startswith("QL-CLICK-"))
total = sum(st.values())
summary = json.loads(OUT.read_text(encoding="utf-8"))
summary.update(
    {
        "CLICKABLE_CONTROLS_TOTAL": total,
        "PASS": st.get("PASS", 0),
        "INTENTIONALLY_DISABLED": st.get("INTENTIONALLY_DISABLED", 0),
        "NOT_APPLICABLE": st.get("NOT_APPLICABLE", 0),
        "UNKNOWN": st.get("UNKNOWN", 0),
        "BROKEN": st.get("BROKEN", 0),
        "PLACEHOLDER": 0,
        "DEAD_LINK": 0,
        "MISSING_BACKEND": 0,
        "MISSING_FRONTEND": 0,
        "WRONG_PERMISSION": 0,
        "WRONG_STATE": 0,
    }
)
summary["MATH_OK"] = (
    summary["UNKNOWN"] == 0
    and summary["BROKEN"] == 0
    and summary["PASS"] + summary["INTENTIONALLY_DISABLED"] + summary["NOT_APPLICABLE"] == total
)
data["evidence"] = ev
data["summary"] = summary
EVID.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
text = LEDGER.read_text(encoding="utf-8")
text = re.sub(
    r"(\| QL-CLICK-0025 \|.*\| )\*\*[A-Z_]+\*\* \|",
    r"\1**" + ev["QL-CLICK-0025"]["FINAL_STATUS"] + r"** |",
    text,
)
for name in (
    "CLICKABLE_CONTROLS_TOTAL",
    "PASS",
    "INTENTIONALLY_DISABLED",
    "NOT_APPLICABLE",
    "UNKNOWN",
    "BROKEN",
):
    text = re.sub(rf"{name}=\d+", f"{name}={summary[name]}", text, count=1)
text = re.sub(r"MATH_OK=\w+", f"MATH_OK={summary['MATH_OK']}", text, count=1)
LEDGER.write_text(text, encoding="utf-8")
print(json.dumps({k: summary[k] for k in ("CLICKABLE_CONTROLS_TOTAL", "PASS", "INTENTIONALLY_DISABLED", "NOT_APPLICABLE", "UNKNOWN", "BROKEN", "MATH_OK")}, indent=2))
raise SystemExit(0 if summary["MATH_OK"] else 1)

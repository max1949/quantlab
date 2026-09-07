"""QLN-6 Phase A: inspect historical backtests in business SQL for recoverable strategy semantics."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

path = Path(r"C:\Users\Administrator\quantlab_business_inserts_pg10.sql")
text = path.read_text(encoding="utf-8", errors="replace")

# Find backtests insert header
bt_lines = [ln for ln in text.splitlines() if "INSERT INTO quantlab.backtests" in ln]
print(f"backtest_insert_lines={len(bt_lines)}")
if bt_lines:
    print("HEADER_SAMPLE:", bt_lines[0][:500])
    print("---")
    # show column list
    m = re.search(r"INSERT INTO quantlab\.backtests \(([^)]+)\)", bt_lines[0])
    if m:
        cols = [c.strip() for c in m.group(1).split(",")]
        print("COLUMNS:", cols)


def split_sql_values(values_blob: str) -> list:
    """Split a SQL VALUES tuple respecting quotes and nested braces."""
    out: list[str | None] = []
    i = 0
    n = len(values_blob)
    while i < n:
        while i < n and values_blob[i] in " \t\n\r,":
            i += 1
        if i >= n:
            break
        if values_blob.startswith("NULL", i) and (i + 4 >= n or values_blob[i + 4] in ",)"):
            out.append(None)
            i += 4
            continue
        if values_blob[i] == "'":
            i += 1
            buf = []
            while i < n:
                ch = values_blob[i]
                if ch == "'" and i + 1 < n and values_blob[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                if ch == "'":
                    i += 1
                    break
                if ch == "\\" and i + 1 < n:
                    buf.append(values_blob[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
            out.append("".join(buf))
            continue
        # unquoted number / true / false / uuid without quotes rare
        j = i
        while j < n and values_blob[j] not in ",)":
            j += 1
        out.append(values_blob[i:j].strip())
        i = j
    return out


records = []
for ln in bt_lines:
    hm = re.search(r"INSERT INTO quantlab\.backtests \(([^)]+)\)\s*VALUES\s*\((.*)\);\s*$", ln, re.I | re.S)
    if not hm:
        # multi-line unlikely; try looser
        hm = re.search(r"INSERT INTO quantlab\.backtests \(([^)]+)\)\s*VALUES\s*\((.*)\)\s*;?\s*$", ln, re.I | re.S)
    if not hm:
        print("PARSE_FAIL_LINE", ln[:200])
        continue
    cols = [c.strip() for c in hm.group(1).split(",")]
    vals = split_sql_values(hm.group(2))
    if len(vals) < len(cols):
        print(f"short_vals cols={len(cols)} vals={len(vals)}")
        continue
    rec = dict(zip(cols, vals[: len(cols)]))
    records.append(rec)

print(f"parsed_backtests={len(records)}")
for i, r in enumerate(records):
    keys_of_interest = [
        "id",
        "project_id",
        "factor_id",
        "status",
        "symbol",
        "timeframe",
        "config",
        "params",
        "metrics",
        "engine",
        "name",
        "notes",
        "spec",
        "strategy_spec",
        "code",
        "entry",
        "exit",
    ]
    present = {k: (r.get(k)[:80] + "...") if isinstance(r.get(k), str) and len(r.get(k) or "") > 80 else r.get(k) for k in r if k in keys_of_interest or "param" in k or "config" in k or "metric" in k or "symbol" in k or "factor" in k or "engine" in k}
    print(f"\n=== BT[{i}] keys={list(r.keys())}")
    for k, v in present.items():
        print(f"  {k}={v!r}")
    # try parse config/params json
    for jk in ("config", "params", "metrics", "result", "settings"):
        raw = r.get(jk)
        if not raw:
            continue
        try:
            obj = json.loads(raw.replace("''", "'")) if raw.startswith("{") or raw.startswith("[") else None
        except Exception as e:
            print(f"  {jk}_json_err={e}")
            obj = None
        if isinstance(obj, dict):
            print(f"  {jk}_json_keys={sorted(obj.keys())}")
            for sk in ("entry", "exit", "signal", "strategy", "rules", "side", "direction", "sizing", "risk", "stop", "take_profit", "template", "factor_type", "code", "logic"):
                if sk in obj:
                    print(f"    {jk}.{sk}={obj[sk]!r}"[:200])

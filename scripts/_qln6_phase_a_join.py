"""QLN-6 Phase A: join backtests ↔ factors ↔ snapshots; assess recoverable semantics."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

path = Path(r"C:\Users\Administrator\quantlab_business_inserts_pg10.sql")
text = path.read_text(encoding="utf-8", errors="replace")


def split_sql_values(values_blob: str) -> list:
    out: list = []
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
            buf: list[str] = []
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
        j = i
        while j < n and values_blob[j] not in ",)":
            j += 1
        out.append(values_blob[i:j].strip())
        i = j
    return out


def parse_table(table: str) -> list[dict]:
    lines = [ln for ln in text.splitlines() if f"INSERT INTO quantlab.{table} " in ln]
    records = []
    for ln in lines:
        m = re.search(
            rf"INSERT INTO quantlab\.{table} \(([^)]+)\)\s*VALUES\s*\((.*)\);\s*$",
            ln,
            re.I | re.S,
        )
        if not m:
            print(f"PARSE_FAIL {table} {ln[:120]}")
            continue
        cols = [c.strip() for c in m.group(1).split(",")]
        vals = split_sql_values(m.group(2))
        records.append(dict(zip(cols, vals[: len(cols)])))
    return records


tables = Counter(re.findall(r"INSERT INTO quantlab\.(\w+)", text))
print("ALL_TABLES", dict(tables))

factors = {r["id"]: r for r in parse_table("factors")}
bts = parse_table("backtests")
projects = {r["id"]: r for r in parse_table("research_projects")}
snaps = {}
for tname in ("data_snapshots", "market_snapshots", "snapshots"):
    if tables.get(tname):
        for r in parse_table(tname):
            snaps[r["id"]] = r
        print(f"loaded_{tname}={len(snaps)}")

print(f"factors={len(factors)} backtests={len(bts)} projects={len(projects)} snaps={len(snaps)}")

# factor template diversity used by backtests
rows = []
for bt in bts:
    f = factors.get(bt["factor_id"])
    snap = snaps.get(bt.get("snapshot_id")) if bt.get("snapshot_id") else None
    cost = json.loads(bt["cost_config"]) if bt.get("cost_config") else {}
    metrics = json.loads(bt["metrics"]) if bt.get("metrics") else {}
    report = None
    if bt.get("report"):
        try:
            report = json.loads(bt["report"])
        except Exception:
            report = {"_raw_prefix": bt["report"][:200]}
    spec = None
    if f and f.get("spec"):
        try:
            spec = json.loads(f["spec"])
        except Exception:
            spec = {"_raw": f["spec"][:200]}
    proj = projects.get(f.get("project_id")) if f and f.get("project_id") else None
    rows.append(
        {
            "bt_id": bt["id"],
            "symbol": bt["symbol"],
            "status": bt["status"],
            "factor_id": bt["factor_id"],
            "factor_name": f.get("name") if f else None,
            "kind": f.get("kind") if f else None,
            "template_type": f.get("template_type") if f else None,
            "project_id": f.get("project_id") if f else None,
            "project_name": proj.get("name") if proj else None,
            "spec": spec,
            "cost": cost,
            "metrics": {
                "sharpe": metrics.get("sharpe"),
                "total_return": metrics.get("total_return"),
                "trade_count": metrics.get("trade_count"),
                "max_drawdown": metrics.get("max_drawdown"),
            },
            "report_keys": sorted(report.keys()) if isinstance(report, dict) else None,
            "report_sample": {
                k: report.get(k)
                for k in (
                    "timeframe",
                    "symbol",
                    "factor_kind",
                    "factor_spec",
                    "cost_config",
                    "snapshot",
                    "methodology",
                    "assumptions",
                )
                if isinstance(report, dict) and k in report
            }
            if report
            else None,
            "snap_timeframe": snap.get("timeframe") if snap else None,
            "snap_symbol": snap.get("symbol") if snap else None,
            "snap_hash": snap.get("content_hash") if snap else None,
            "snap_rows": snap.get("rows") if snap else None,
            "snap_start": snap.get("start_date") if snap else None,
            "snap_end": snap.get("end_date") if snap else None,
        }
    )

out = Path(r"C:\Users\Administrator\quantlab\docs\governance\qln6\_phase_a_join.json")
out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"wrote {out} n={len(rows)}")

print("SYMBOLS", Counter(r["symbol"] for r in rows))
print("TEMPLATES", Counter(r["template_type"] for r in rows))
print("KINDS", Counter(r["kind"] for r in rows))
print("PROJECTS", Counter(r["project_name"] for r in rows).most_common(15))
print("HAS_SNAP_TF", sum(1 for r in rows if r["snap_timeframe"]))
print("HAS_REPORT_SNAP", sum(1 for r in rows if r.get("report_sample") and "snapshot" in (r["report_sample"] or {})))

# uniqueness of factor specs among backtested factors
uniq = {}
for r in rows:
    key = json.dumps(
        {"kind": r["kind"], "template": r["template_type"], "spec": r["spec"]},
        sort_keys=True,
        ensure_ascii=False,
    )
    uniq.setdefault(key, []).append(r["bt_id"][:8])
print(f"UNIQUE_FACTOR_SEMANTICS={len(uniq)}")
for i, (k, ids) in enumerate(list(uniq.items())[:12]):
    obj = json.loads(k)
    print(f"  U[{i}] n_bts={len(ids)} kind={obj['kind']} tmpl={obj['template']} spec={json.dumps(obj['spec'], ensure_ascii=False)[:160]}")

# sample full report
for r in rows:
    if r.get("report_sample"):
        print("SAMPLE_REPORT", json.dumps(r["report_sample"], ensure_ascii=False)[:800])
        break

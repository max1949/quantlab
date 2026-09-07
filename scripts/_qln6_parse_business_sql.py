"""Parse business SQL dump for strategy/factor inventory (read-only)."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

path = Path(r"C:\Users\Administrator\quantlab_business_inserts_pg10.sql")
text = path.read_text(encoding="utf-8", errors="replace")
tables = Counter(re.findall(r"INSERT INTO quantlab\.(\w+)", text))
print("TABLE_INSERTS")
for k, v in tables.most_common(50):
    print(f"  {k}: {v}")

for pat in (
    "strategy_spec",
    "paper_run",
    "paper_orders",
    "research_project",
    "backtest",
    "strategy_package",
):
    print(f"mention_{pat}={text.lower().count(pat)}")

flines = [ln for ln in text.splitlines() if "INSERT INTO quantlab.factors" in ln]
print(f"factor_insert_lines={len(flines)}")

# Column order from first insert header
# factors (id, owner_id, name, kind, template_type, spec, version, created_at, updated_at, project_id, ...)
parsed = []
for ln in flines:
    # Split VALUES (
    if "VALUES" not in ln.upper():
        continue
    # Naive CSV-ish parse of quoted strings at start of values
    vals = re.findall(r"'((?:\\'|[^'])*)'|NULL|([0-9a-f-]{36})", ln, flags=re.I)
    # flatten
    flat = []
    for a, b in vals:
        flat.append(a if a else b)
    # After UUID id, UUID owner, name, kind, template_type
    if len(flat) >= 5:
        parsed.append(
            {
                "id": flat[0],
                "owner_id": flat[1],
                "name": flat[2],
                "kind": flat[3],
                "template_type": flat[4],
            }
        )

print(f"factors_parsed={len(parsed)}")
names = Counter(p["name"] for p in parsed)
kinds = Counter(p["kind"] for p in parsed)
tmpls = Counter(p["template_type"] for p in parsed)
owners = Counter(p["owner_id"] for p in parsed)
print("TOP_NAMES", names.most_common(20))
print("KINDS", kinds.most_common())
print("TEMPLATES", tmpls.most_common())
print("OWNERS", len(owners), owners.most_common(5))

# Any strategy-like tables
for t in tables:
    if "strateg" in t.lower() or "spec" in t.lower() or "paper" in t.lower():
        print(f"strategyish_table {t}: {tables[t]}")

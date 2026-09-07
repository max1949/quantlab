"""Risk clusters from correlation graph."""

from __future__ import annotations

from typing import Any


def cluster_by_correlation(
    pairs: list[dict[str, Any]],
    *,
    threshold: float = 0.7,
) -> list[list[str]]:
    """Union-find style clusters for |corr| >= threshold."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    nodes: set[str] = set()
    for p in pairs:
        a, b = str(p["a"]), str(p["b"])
        nodes.add(a)
        nodes.add(b)
        if abs(float(p["corr"])) >= threshold:
            union(a, b)

    groups: dict[str, list[str]] = {}
    for n in sorted(nodes):
        groups.setdefault(find(n), []).append(n)
    return [sorted(v) for v in groups.values()]

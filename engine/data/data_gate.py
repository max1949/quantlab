"""Formal DATA_GATE for Strategy Spec / Nautilus backtest entry."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

GateStatus = Literal["PASS", "WARN", "FAIL"]


@dataclass
class DataProvenance:
    provider: str = "unknown"
    broker: str | None = None
    venue: str | None = None
    symbol: str = ""
    instrument: str = ""
    timezone: str = "UTC"
    price_type: str = "last"
    frequency: str = "15m"
    broker_specific: bool = False
    start: str | None = None
    end: str | None = None
    raw_hash: str | None = None
    normalized_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DataGateResult:
    status: GateStatus
    issues_zh: list[str] = field(default_factory=list)
    issues_tech: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def passed(self) -> bool:
        return self.status != "FAIL"


def _frame_hash(df: pd.DataFrame) -> str:
    payload = pd.util.hash_pandas_object(df, index=True).to_numpy(dtype=np.uint64)
    return hashlib.sha256(payload.tobytes()).hexdigest()


def run_data_gate(
    df: pd.DataFrame,
    *,
    provenance: DataProvenance | dict[str, Any] | None = None,
    timeframe: str | None = None,
    require_broker_specific: bool = False,
) -> DataGateResult:
    """Return PASS / WARN / FAIL before formal BacktestRun."""
    prov = (
        DataProvenance(**provenance)
        if isinstance(provenance, dict)
        else (provenance or DataProvenance())
    )
    if timeframe:
        prov.frequency = timeframe

    issues_zh: list[str] = []
    issues_tech: list[str] = []
    stats: dict[str, Any] = {"rows": int(len(df))}

    if df is None or len(df) == 0:
        return DataGateResult(
            status="FAIL",
            issues_zh=["没有可用行情数据。"],
            issues_tech=["empty_dataframe"],
            provenance=prov.to_dict(),
        )

    work = df.copy()
    if not isinstance(work.index, pd.DatetimeIndex):
        if "datetime" in work.columns:
            work = work.set_index(pd.to_datetime(work["datetime"], utc=True))
        else:
            issues_zh.append("缺少时间索引，无法确认时间顺序。")
            issues_tech.append("missing_datetime_index")

    if isinstance(work.index, pd.DatetimeIndex):
        if work.index.tz is None:
            issues_zh.append("数据时区需要确认（当前无时区信息）。")
            issues_tech.append("timezone_naive")
            stats["timezone"] = None
        else:
            stats["timezone"] = str(work.index.tz)

        if not work.index.is_monotonic_increasing:
            issues_zh.append("时间戳不是递增顺序。")
            issues_tech.append("non_monotonic_timestamps")

        dup = int(work.index.duplicated().sum())
        stats["duplicate_timestamps"] = dup
        if dup > 0:
            issues_zh.append(f"发现 {dup} 处重复时间戳。")
            issues_tech.append(f"duplicates={dup}")

        stats["start"] = str(work.index.min())
        stats["end"] = str(work.index.max())
        prov.start = stats["start"]
        prov.end = stats["end"]

    for col in ("open", "high", "low", "close"):
        if col not in work.columns:
            issues_zh.append(f"缺少价格列：{col}。")
            issues_tech.append(f"missing_column:{col}")
            continue
        series = pd.to_numeric(work[col], errors="coerce")
        bad = int((series.isna() | (series <= 0)).sum())
        stats[f"invalid_{col}"] = bad
        if bad > 0:
            issues_zh.append(f"{col} 存在 {bad} 处无效或非正价格。")
            issues_tech.append(f"invalid_price:{col}={bad}")

    if "volume" in work.columns:
        vol = pd.to_numeric(work["volume"], errors="coerce")
        neg = int((vol < 0).sum())
        stats["invalid_volume"] = neg
        if neg > 0:
            issues_zh.append(f"成交量存在 {neg} 处负数。")
            issues_tech.append(f"invalid_volume={neg}")

    missing = int(work.isna().sum().sum())
    stats["missing_values"] = missing
    if missing > 0:
        issues_zh.append(f"发现 {missing} 处缺失值。")
        issues_tech.append(f"missing_values={missing}")

    # FX/CFD/XAUUSD broker-specific provenance
    inst = (prov.instrument or prov.symbol or "").upper()
    fx_like = any(
        x in inst
        for x in ("EUR", "USD", "GBP", "XAU", "CFD", "USDT")
    ) or "/" in (prov.instrument or "")
    if fx_like:
        prov.broker_specific = True
        if require_broker_specific and not (prov.broker or prov.provider):
            issues_zh.append("外汇/CFD/贵金属数据必须标注来源券商或数据提供方。")
            issues_tech.append("missing_broker_specific_provenance")

    if not prov.normalized_hash:
        try:
            prov.normalized_hash = _frame_hash(work)
        except Exception:  # noqa: BLE001
            prov.normalized_hash = None

    fail_tokens = {
        "empty_dataframe",
        "missing_datetime_index",
        "non_monotonic_timestamps",
        "missing_broker_specific_provenance",
    }
    hard_fail = any(
        any(tok in t for tok in fail_tokens) or t.startswith("invalid_price:")
        for t in issues_tech
    )
    if hard_fail or any(k.startswith("invalid_price") and stats.get(k, 0) > 0 for k in stats):
        # invalid prices already captured
        if any(s.startswith("invalid_price") for s in issues_tech) or hard_fail:
            status: GateStatus = "FAIL"
        else:
            status = "WARN"
    elif issues_zh:
        status = "WARN"
    else:
        status = "PASS"

    # Strengthen: non-monotonic / invalid price / empty => FAIL
    if any(
        t.startswith("invalid_price")
        or t in {"empty_dataframe", "missing_datetime_index", "non_monotonic_timestamps"}
        or t == "missing_broker_specific_provenance"
        for t in issues_tech
    ):
        status = "FAIL"

    return DataGateResult(
        status=status,
        issues_zh=issues_zh,
        issues_tech=issues_tech,
        stats=stats,
        provenance=prov.to_dict(),
        evidence={
            "gate": "DATA_GATE",
            "frequency": prov.frequency,
            "broker_specific": prov.broker_specific,
        },
    )


def user_facing_data_gate_message(result: DataGateResult) -> dict[str, Any]:
    if result.status == "PASS":
        return {
            "title_zh": "数据检查通过",
            "body_zh": "可以进入正式回测。",
            "status": result.status,
            "issues_zh": [],
        }
    title = "数据检查没有通过。" if result.status == "FAIL" else "数据检查有警告。"
    return {
        "title_zh": title,
        "body_zh": "当前不建议正式回测。" if result.status == "FAIL" else "可以谨慎继续研究回测。",
        "status": result.status,
        "issues_zh": result.issues_zh,
        "actions_zh": ["让系统尝试修复", "更换数据源", "更换品种"],
    }

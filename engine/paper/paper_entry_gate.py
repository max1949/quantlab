"""Paper entry gate chain: must reach PAPER_READY for bound spec version."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

GateStatus = Literal["PASS", "WARN", "FAIL"]


@dataclass
class PaperEntryGateResult:
    status: GateStatus
    paper_ready: bool
    strategy_spec_id: str
    strategy_spec_version: str
    strategy_spec_hash: str
    checks: dict[str, GateStatus] = field(default_factory=dict)
    detail_zh: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_paper_entry_gate(
    *,
    strategy_spec_id: str,
    strategy_spec_version: str,
    strategy_spec_hash: str,
    data_gate_status: str,
    backtest_pass: bool,
    validation_pass: bool,
    robustness_pass: bool,
    paper_ready_version: str | None,
    paper_ready_hash: str | None,
) -> PaperEntryGateResult:
    checks: dict[str, GateStatus] = {}
    detail: list[str] = []

    def _mark(name: str, ok: bool, msg: str) -> None:
        checks[name] = "PASS" if ok else "FAIL"
        detail.append(msg)

    _mark("DATA_PASS", data_gate_status in {"PASS", "WARN"}, f"数据门：{data_gate_status}")
    _mark("BACKTEST_PASS", backtest_pass, "回测门：" + ("通过" if backtest_pass else "未通过"))
    _mark("VALIDATION_PASS", validation_pass, "验证门：" + ("通过" if validation_pass else "未通过"))
    _mark(
        "ROBUSTNESS_PASS",
        robustness_pass,
        "稳健性门：" + ("通过" if robustness_pass else "未通过"),
    )

    version_match = (
        paper_ready_version == strategy_spec_version
        and paper_ready_hash == strategy_spec_hash
        and paper_ready_version is not None
    )
    checks["PAPER_READY"] = "PASS" if version_match else "FAIL"
    if not version_match:
        detail.append(
            f"PAPER_READY 未绑定当前版本 {strategy_spec_version}；"
            f"已登记版本={paper_ready_version or '无'}"
        )
    else:
        detail.append(f"PAPER_READY 已绑定 {strategy_spec_version}")

    all_pass = all(v == "PASS" for v in checks.values())
    status: GateStatus = "PASS" if all_pass else "FAIL"
    return PaperEntryGateResult(
        status=status,
        paper_ready=all_pass,
        strategy_spec_id=strategy_spec_id,
        strategy_spec_version=strategy_spec_version,
        strategy_spec_hash=strategy_spec_hash,
        checks=checks,
        detail_zh=detail,
    )

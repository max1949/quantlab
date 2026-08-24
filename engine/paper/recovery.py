"""Restart recovery helpers — prevent duplicate entries after crash."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecoverySnapshot:
    has_open_position: bool
    open_side: str | None
    open_quantity: float
    recovered_from_crash: bool
    restart_count: int


def should_allow_new_entry(
    *,
    signal_side: str | None,
    snapshot: RecoverySnapshot,
    allow_exit: bool = True,
) -> tuple[bool, str]:
    """Block duplicate economic entry after restart if position already open."""
    if not signal_side:
        return False, "无有效信号"
    if snapshot.has_open_position:
        same_side = snapshot.open_side == signal_side
        if same_side:
            return False, "重启后已有同向持仓，禁止重复开仓"
        if allow_exit:
            return True, "反向信号允许平仓"
        return False, "已有持仓"
    return True, "允许新开仓"

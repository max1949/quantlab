"""Server-side kill switch checks for paper sandbox."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

KillVerdict = Literal["ALLOW", "DENY"]


class KillSwitchScope(str, Enum):
    GLOBAL = "GLOBAL"
    PAPER_RUN = "PAPER_RUN"
    STRATEGY = "STRATEGY"


@dataclass
class KillSwitchState:
    global_active: bool = False
    paper_run_active: bool = False
    strategy_active: bool = False
    reason: str = ""


def check_kill_switch(state: KillSwitchState) -> KillVerdict:
    if state.global_active or state.paper_run_active or state.strategy_active:
        return "DENY"
    return "ALLOW"

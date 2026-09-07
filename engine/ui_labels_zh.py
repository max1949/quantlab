"""Chinese human-readable labels for Evidence OS UI (canonical enums unchanged)."""

from __future__ import annotations

from typing import Any


DECISION_ZH: dict[str, dict[str, str]] = {
    "PROMOTE": {
        "label_zh": "建议晋级",
        "summary_zh": "证据达到晋级门槛，可进入模拟交易观察；不等于实盘授权。",
        "next_zh": "进入模拟交易（PaperRun）收集成交与净值证据，再看 Shadow。",
    },
    "HOLD": {
        "label_zh": "证据不足，暂缓",
        "summary_zh": "关键闸门未齐或现实分/研究债未达标，暂不晋级。",
        "next_zh": "补齐缺失证据（样本外 / Walk-Forward / 压力测试），或简化假设后重跑。",
    },
    "KILL": {
        "label_zh": "淘汰",
        "summary_zh": "硬闸门失败或过拟合/研究债过高，不应继续投入资本注意力。",
        "next_zh": "写入坟场与研究记忆；如需再试，必须换假设或换版本，禁止同参硬磨。",
    },
}

GATE_FLAG_ZH = {
    "PASS": "通过",
    "FAIL": "未通过",
    "INSUFFICIENT": "证据不足",
}

LIVE_READINESS_ZH = {
    "PASS": {
        "label_zh": "工程上具备申请实盘资格",
        "caveat_zh": "具备申请实盘资格 ≠ 已允许实盘。仍需 Owner 单独授权与可用券商能力。",
    },
    "HOLD": {
        "label_zh": "实盘资格暂缓",
        "caveat_zh": "前置证据或券商能力未齐，不得进入实盘。",
    },
    "DENY": {
        "label_zh": "拒绝实盘资格",
        "caveat_zh": "关键闸门失败；禁止实盘。",
    },
}


def explain_decision(decision: str, reasons: list[str] | None = None) -> dict[str, Any]:
    base = DECISION_ZH.get(str(decision).upper()) or {
        "label_zh": str(decision),
        "summary_zh": "未知判定，请联系研究运维。",
        "next_zh": "回到证据流水线重跑。",
    }
    return {
        "decision": str(decision).upper(),
        "label_zh": base["label_zh"],
        "summary_zh": base["summary_zh"],
        "why_zh": list(reasons or []),
        "next_zh": base["next_zh"],
        "live_note_zh": "证据判定与模拟交易均不构成实盘授权。REAL_MONEY=NO。",
    }


def gate_flags_zh(gates: dict[str, Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    names = {
        "backtest": "回测",
        "oos": "样本外（OOS）",
        "walk_forward": "滚动样本外（Walk-Forward）",
        "fee_stress": "费率压力",
        "slippage_stress": "滑点压力",
        "parameter_sensitivity": "参数敏感性",
        "regime_split": "制度分段",
        "extreme_period": "极端时段",
    }
    for k, v in (gates or {}).items():
        out[k] = {
            "name_zh": names.get(k, k),
            "flag": str(v),
            "flag_zh": GATE_FLAG_ZH.get(str(v), str(v)),
        }
    return out

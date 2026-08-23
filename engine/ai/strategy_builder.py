"""AI Quant Copilot — Natural Language → Strategy Spec draft (no live authority).

Phase 3: deterministic rule-based parser for Chinese trading ideas.
LLM providers may wrap this later via AIProvider; they cannot bypass gates.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from engine.strategies.spec import StrategySpec
from engine.strategies.validate import validate_spec


@dataclass
class AmbiguityItem:
    field: str
    question_zh: str
    assumed_value: str | None = None


@dataclass
class StrategyBuilderResult:
    ambiguous: bool
    deployable: bool
    questions: list[AmbiguityItem] = field(default_factory=list)
    assumed_values: list[str] = field(default_factory=list)
    confirmation_zh: list[str] = field(default_factory=list)
    draft_spec: dict[str, Any] | None = None
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


_INSTRUMENT_MAP = {
    "黄金": ("XAUUSD", True),  # ambiguous venue/CFD vs futures
    "金": ("XAUUSD", True),
    "xauusd": ("XAUUSD", False),
    "gc": ("GC", True),
    "欧元": ("EUR/USD", False),
    "eurusd": ("EUR/USD", False),
    "欧元美元": ("EUR/USD", False),
    "比特币": ("BTCUSDT", True),
    "btc": ("BTCUSDT", True),
}


def _detect_instrument(text: str) -> tuple[str | None, bool, AmbiguityItem | None]:
    lower = text.lower()
    for key, (symbol, amb) in _INSTRUMENT_MAP.items():
        if key in text or key in lower:
            q = None
            if amb:
                q = AmbiguityItem(
                    field="market.instrument",
                    question_zh=f"「{key}」对应哪个具体品种代码？当前暂按 {symbol} 作为研究假设。",
                    assumed_value=symbol,
                )
            return symbol, amb, q
    return None, True, AmbiguityItem(
        field="market.instrument",
        question_zh="要交易哪个品种？（例如 XAUUSD、EUR/USD、RB888）",
        assumed_value=None,
    )


def _detect_timeframe(text: str) -> tuple[str | None, AmbiguityItem | None]:
    m = re.search(r"(\d+)\s*分钟", text)
    if m:
        return f"{m.group(1)}m", None
    m = re.search(r"(\d+)\s*小时", text)
    if m:
        return f"{m.group(1)}h", None
    if "日线" in text or "每天" in text:
        return "1d", None
    if re.search(r"\b(\d+)m\b", text.lower()):
        return re.search(r"\b(\d+)m\b", text.lower()).group(0), None  # type: ignore[union-attr]
    return None, AmbiguityItem(
        field="market.timeframe",
        question_zh="使用哪个K线周期？（例如 15分钟、1小时、日线）",
        assumed_value="15m",
    )


def _detect_ema_cross(text: str) -> tuple[dict[str, int] | None, list[AmbiguityItem]]:
    questions: list[AmbiguityItem] = []
    m = re.search(r"EMA\s*(\d+)\s*.{0,6}EMA\s*(\d+)", text, flags=re.I)
    if not m:
        m = re.search(r"均线\s*(\d+)\s*.{0,6}均线\s*(\d+)", text)
    if m:
        fast, slow = int(m.group(1)), int(m.group(2))
        if fast > slow:
            fast, slow = slow, fast
        return {"fast": fast, "slow": slow}, questions
    if "突破" in text and "EMA" not in text.upper() and "均线" not in text:
        questions.append(
            AmbiguityItem(
                field="entry.long",
                question_zh="「突破」具体指什么？前高、当天高点、Donchian，还是过去N根K线最高价？",
                assumed_value=None,
            )
        )
        return None, questions
    if any(k in text for k in ("均线", "EMA", "上穿", "金叉")):
        questions.append(
            AmbiguityItem(
                field="entry.ema",
                question_zh="请给出快慢均线周期（例如 EMA20 上穿 EMA60）。",
                assumed_value="EMA10/EMA20",
            )
        )
        return {"fast": 10, "slow": 20}, questions
    return None, [
        AmbiguityItem(
            field="entry",
            question_zh="入场规则是什么？（例如 EMA20 上穿 EMA60）",
            assumed_value=None,
        )
    ]


def _detect_risk(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "risk_per_trade": None,
        "daily_loss_limit": None,
        "max_consecutive_losses": None,
        "stop_atr": None,
        "tp_atr": None,
        "adx_min": None,
    }
    m = re.search(r"每笔.*?亏\s*([0-9.]+)\s*%", text)
    if m:
        out["risk_per_trade"] = float(m.group(1)) / 100.0
    m = re.search(r"每天.*?亏\s*([0-9.]+)\s*%", text)
    if m:
        out["daily_loss_limit"] = float(m.group(1)) / 100.0
    m = re.search(r"连续亏\s*(\d+)\s*笔", text)
    if m:
        out["max_consecutive_losses"] = int(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*倍?\s*ATR.*?止损", text, flags=re.I)
    if m:
        out["stop_atr"] = float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*倍?\s*ATR.*?止盈", text, flags=re.I)
    if m:
        out["tp_atr"] = float(m.group(1))
    m = re.search(r"ADX\s*(?:大于|>|≥)\s*(\d+)", text, flags=re.I)
    if m:
        out["adx_min"] = int(m.group(1))
    return out


def build_strategy_from_chinese(text: str, *, author: str = "user") -> StrategyBuilderResult:
    """Parse Chinese idea → ambiguity list + optional research draft Spec.

    Never sets deployable=True. Never permits LIVE.
    """
    text = (text or "").strip()
    if not text:
        return StrategyBuilderResult(
            ambiguous=True,
            deployable=False,
            blocked_reason="empty_input",
            questions=[AmbiguityItem("input", "请用中文描述你的交易想法。")],
        )

    questions: list[AmbiguityItem] = []
    assumed: list[str] = []

    instrument, inst_amb, inst_q = _detect_instrument(text)
    if inst_q:
        questions.append(inst_q)
        if inst_q.assumed_value:
            assumed.append(f"instrument={inst_q.assumed_value}")
    if instrument is None:
        return StrategyBuilderResult(
            ambiguous=True,
            deployable=False,
            questions=questions,
            assumed_values=assumed,
            blocked_reason="missing_instrument",
        )

    timeframe, tf_q = _detect_timeframe(text)
    if tf_q:
        questions.append(tf_q)
        timeframe = timeframe or tf_q.assumed_value
        if tf_q.assumed_value:
            assumed.append(f"timeframe={tf_q.assumed_value}")
    if timeframe is None:
        timeframe = "15m"
        assumed.append("timeframe=15m")

    ema, ema_qs = _detect_ema_cross(text)
    questions.extend(ema_qs)
    if ema and any(q.assumed_value for q in ema_qs):
        assumed.append(f"ema={ema['fast']}/{ema['slow']}")

    risk = _detect_risk(text)
    hard_missing_entry = ema is None and any(q.assumed_value is None for q in ema_qs)
    ambiguous = bool(questions) or inst_amb or hard_missing_entry or ema is None

    if ema is None:
        return StrategyBuilderResult(
            ambiguous=True,
            deployable=False,
            questions=questions,
            assumed_values=assumed,
            blocked_reason="missing_entry_rule",
            confirmation_zh=["还不能生成可回测策略，请先回答入场规则相关问题。"],
        )

    # Research draft allowed with ASSUMED_VALUE markers even if ambiguous.
    sid = f"ai_draft_{uuid.uuid4().hex[:8]}"
    stop_type, stop_val = ("none", None)
    tp_type, tp_val = ("none", None)
    if risk["stop_atr"] is not None:
        stop_type, stop_val = "atr_mult", risk["stop_atr"]
    else:
        assumed.append("stop_loss=none")
        questions.append(
            AmbiguityItem("stop_loss", "止损规则是什么？（例如 2倍ATR）", assumed_value="none")
        )
        ambiguous = True
    if risk["tp_atr"] is not None:
        tp_type, tp_val = "atr_mult", risk["tp_atr"]

    draft = {
        "strategy": {
            "id": sid,
            "version": "v1",
            "name": f"AI草稿-{instrument}-{timeframe}",
            "description": text[:500],
            "author": author,
            "status": "DRAFT",
            "ai_generated": True,
            "user_approved": False,
            "ambiguous": ambiguous,
            "deployable": False,
            "assumed_values": assumed,
            "created_by": "ai_strategy_builder",
        },
        "market": {
            "instrument": instrument,
            "venue": "SIM",
            "asset_class": "FX" if "/" in instrument or instrument in {"XAUUSD", "EURUSD"} else "OTHER",
            "timeframe": timeframe,
            "timezone": "UTC",
        },
        "entry": {
            "long": {
                "conditions": [
                    {"type": "ema_cross", "params": {"fast": ema["fast"], "slow": ema["slow"], "direction": "up"}}
                ]
            },
            "short": {
                "conditions": [
                    {"type": "ema_cross", "params": {"fast": ema["fast"], "slow": ema["slow"], "direction": "down"}}
                ]
            },
        },
        "exit": {"conditions": []},
        "stop_loss": {"type": stop_type, "value": stop_val},
        "take_profit": {"type": tp_type, "value": tp_val},
        "position_sizing": {
            "type": "risk_fraction" if risk["risk_per_trade"] else "fixed",
            "risk_per_trade": risk["risk_per_trade"],
            "trade_size": "1000000",
        },
        "risk": {
            "daily_loss_limit": risk["daily_loss_limit"],
            "max_consecutive_losses": risk["max_consecutive_losses"],
            "max_open_positions": 1,
        },
        "execution": {"order_type": "MARKET", "time_in_force": "GTC"},
        "regime": {
            "enabled": risk["adx_min"] is not None,
            "filters": ([{"type": "adx_min", "value": risk["adx_min"]}] if risk["adx_min"] else []),
        },
        "validation": {"required_tests": ["backtest"]},
        "deployment": {"permitted_environments": ["BACKTEST"]},
    }

    spec = validate_spec(draft)
    confirmation = [
        f"品种：{instrument}" + ("（假设值）" if inst_amb else ""),
        f"周期：{timeframe}",
        f"入场：EMA{ema['fast']} 与 EMA{ema['slow']} 交叉",
        f"止损：{stop_type}" + (f"={stop_val}" if stop_val is not None else ""),
        f"止盈：{tp_type}" + (f"={tp_val}" if tp_val is not None else ""),
        "环境：仅 BACKTEST（不可直接实盘）",
        "请确认以上规则后再运行回测。",
    ]
    if ambiguous:
        confirmation.insert(0, "仍有歧义或假设值：草稿仅可用于研究，不能部署。")

    return StrategyBuilderResult(
        ambiguous=ambiguous,
        deployable=False,
        questions=questions,
        assumed_values=assumed,
        confirmation_zh=confirmation,
        draft_spec=spec.canonical_dict(),
        blocked_reason=None,
    )


def confirm_draft(draft_spec: dict[str, Any], *, user_approved_rules: bool) -> StrategySpec:
    """User confirms structured rules → RESEARCH status still non-LIVE."""
    data = dict(draft_spec)
    data["strategy"] = dict(data["strategy"])
    if not user_approved_rules:
        raise ValueError("user must explicitly confirm strategy rules")
    data["strategy"]["user_approved"] = True
    data["strategy"]["status"] = "RESEARCH"
    # User accepted ASSUMED_VALUE for research only; never auto-deployable / LIVE.
    data["strategy"]["ambiguous"] = False
    data["strategy"]["deployable"] = False
    return validate_spec(data)

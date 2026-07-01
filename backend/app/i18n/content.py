"""Bilingual API copy (en default, zh overlay)."""

from __future__ import annotations

from backend.app.core.locale import Locale

RESEARCH_TEMPLATES: dict[str, dict[Locale, dict]] = {
    "gold-trend": {
        "en": {
            "title": "Gold Trend Study",
            "hypothesis": "Does gold exhibit trend persistence?",
            "description": "Test whether gold (AU) trends can be captured with a momentum factor.",
            "tags": ["trend", "precious metals"],
        },
        "zh": {
            "title": "黄金趋势研究",
            "hypothesis": "黄金价格是否存在趋势延续性?",
            "description": "用动量因子检验黄金 (AU) 的趋势是否可被捕捉。",
            "tags": ["趋势", "贵金属"],
        },
    },
    "commodity-momentum": {
        "en": {
            "title": "Commodity Momentum",
            "hypothesis": "Is momentum effective on rebar (RB)?",
            "description": "Study trend inertia in commodity futures with a momentum factor.",
            "tags": ["momentum", "commodity"],
        },
        "zh": {
            "title": "商品动量研究",
            "hypothesis": "螺纹钢 (RB) 的动量效应是否有效?",
            "description": "用动量因子研究商品期货的趋势惯性。",
            "tags": ["动量", "商品"],
        },
    },
    "vol-regime": {
        "en": {
            "title": "Volatility Regime",
            "hypothesis": "Do volatility states predict return distribution?",
            "description": "Study risk regime shifts on index futures (IF) with a volatility factor.",
            "tags": ["volatility", "index"],
        },
        "zh": {
            "title": "波动率研究",
            "hypothesis": "波动率状态能否预示后续收益分布?",
            "description": "用波动率因子研究股指 (IF) 的风险状态切换。",
            "tags": ["波动率", "股指"],
        },
    },
    "mean-reversion": {
        "en": {
            "title": "Mean Reversion",
            "hypothesis": "Do prices tend to revert after deviating from the mean?",
            "description": "Test mean-reversion behavior with a dedicated factor.",
            "tags": ["mean reversion"],
        },
        "zh": {
            "title": "均值回归研究",
            "hypothesis": "价格偏离均值后是否倾向回归?",
            "description": "用均值回归因子检验价格的回归特性。",
            "tags": ["均值回归"],
        },
    },
    "rsi-study": {
        "en": {
            "title": "RSI Strength Study",
            "hypothesis": "Do RSI extremes contain reversal signals?",
            "description": "Study short-term strength swings on rebar with RSI.",
            "tags": ["RSI", "commodity"],
        },
        "zh": {
            "title": "RSI 强弱研究",
            "hypothesis": "RSI 超买超卖区域是否蕴含反转信号?",
            "description": "用 RSI 因子研究螺纹钢短期强弱切换。",
            "tags": ["RSI", "商品"],
        },
    },
    "sma-cross": {
        "en": {
            "title": "SMA Deviation Study",
            "hypothesis": "Is there a tradable signal when price deviates from its moving average?",
            "description": "Study index pricing deviation with an SMA ratio factor.",
            "tags": ["moving average", "index"],
        },
        "zh": {
            "title": "均线偏离研究",
            "hypothesis": "价格偏离均线后是否存在可交易信号?",
            "description": "用均线偏离因子研究股指定价偏离。",
            "tags": ["均线", "股指"],
        },
    },
    "multi-momentum": {
        "en": {
            "title": "Advanced Momentum",
            "hypothesis": "Is long-window momentum more robust on gold?",
            "description": "Researcher Plus — long-window momentum template.",
            "tags": ["momentum", "advanced"],
        },
        "zh": {
            "title": "进阶动量组合",
            "hypothesis": "长周期动量在黄金上是否更稳健?",
            "description": "研究员会员专属 — 长窗口动量研究模板。",
            "tags": ["动量", "进阶"],
        },
    },
}

FACTOR_TEMPLATES: dict[str, dict[Locale, dict]] = {
    "momentum": {
        "en": {
            "label": "Momentum",
            "description": "Past N-period return; captures trend continuation.",
            "params": {"window": "Lookback window"},
        },
        "zh": {
            "label": "动量因子",
            "description": "过去 N 期收益率, 捕捉趋势延续。",
            "params": {"window": "回看窗口"},
        },
    },
    "sma_ratio": {
        "en": {
            "label": "SMA deviation",
            "description": "Price deviation from N-period moving average.",
            "params": {"window": "MA window"},
        },
        "zh": {
            "label": "均线偏离",
            "description": "价格相对 N 期均线的偏离度。",
            "params": {"window": "均线窗口"},
        },
    },
    "rsi": {
        "en": {
            "label": "RSI strength",
            "description": "Relative strength index (0–100) for overbought/oversold.",
            "params": {"window": "RSI window"},
        },
        "zh": {
            "label": "RSI 强弱",
            "description": "相对强弱指标 (0-100), 衡量超买超卖。",
            "params": {"window": "RSI 窗口"},
        },
    },
    "volatility": {
        "en": {
            "label": "Volatility",
            "description": "Rolling std of returns; measures risk level.",
            "params": {"window": "Vol window"},
        },
        "zh": {
            "label": "波动率",
            "description": "收益率的滚动标准差, 衡量风险水平。",
            "params": {"window": "波动窗口"},
        },
    },
    "mean_reversion": {
        "en": {
            "label": "Mean reversion",
            "description": "Negative z-score vs mean; expects reversion.",
            "params": {"window": "Lookback window"},
        },
        "zh": {
            "label": "均值回归",
            "description": "价格相对均值的负向 z-score, 预期向均值回归。",
            "params": {"window": "回看窗口"},
        },
    },
}

USER_TYPE_LABEL: dict[str, dict[Locale, str]] = {
    "newbie": {"en": "Complete beginner", "zh": "完全新手"},
    "python": {"en": "Python user", "zh": "Python 用户"},
    "trader": {"en": "Experienced trader", "zh": "交易经验用户"},
}

TYPE_INTRO: dict[str, dict[Locale, str]] = {
    "newbie": {
        "en": "No coding needed — we'll guide you through your first study with templates.",
        "zh": "完全不用写代码, 我们带你用模板一步步做出第一个研究。",
    },
    "python": {
        "en": "You know Python — we'll put you on a faster factor and stack track.",
        "zh": "你有 Python 基础, 可以更快上手因子与组合, 我们直接给你硬核路线。",
    },
    "trader": {
        "en": "You know markets — we'll turn intuition into testable factors and conclusions.",
        "zh": "你懂交易, 我们帮你把盘感变成可被验证的因子与研究结论。",
    },
}

STEP_DETAIL: dict[str, dict[Locale, dict[str, str]]] = {
    "create_project": {
        "en": {
            "title": "Create your first research project",
            "action": "Pick a template to set your research theme",
        },
        "zh": {
            "title": "创建你的第一个研究项目",
            "action": "用研究模板一键开局, 定一个研究主题",
        },
    },
    "create_factor": {
        "en": {
            "title": "Build your first factor",
            "action": "Add a template factor (e.g. momentum) and set a window",
        },
        "zh": {
            "title": "造你的第一个因子",
            "action": "在项目下选一个模板因子 (如动量), 填个窗口参数即可",
        },
    },
    "run_backtest": {
        "en": {
            "title": "Run your first backtest",
            "action": "See how the factor performed on historical data",
        },
        "zh": {
            "title": "跑第一次回测",
            "action": "看看这个因子在历史行情上的表现",
        },
    },
    "run_validation": {
        "en": {
            "title": "Run scientific validation (OOS)",
            "action": "Use out-of-sample + walk-forward to check overfitting",
        },
        "zh": {
            "title": "做一次科学验证 (OOS)",
            "action": "用样本外 + Walk-Forward 检验因子是不是过拟合",
        },
    },
    "generate_report": {
        "en": {
            "title": "Generate research report",
            "action": "Combine factor, backtest, and validation into a readable report",
        },
        "zh": {
            "title": "生成研究报告",
            "action": "把因子+回测+验证聚合成一篇人话研究报告",
        },
    },
    "publish_share": {
        "en": {
            "title": "Publish and share your research",
            "action": "Make the project public and share a research card",
        },
        "zh": {
            "title": "发布并分享你的研究",
            "action": "公开项目、生成分享卡片, 让更多人看到你的研究",
        },
    },
    "keep_going": {
        "en": {
            "title": "Keep deepening your research",
            "action": "Try stacks, cross-symbol validation, or a new theme for the ranks",
        },
        "zh": {
            "title": "继续深化研究",
            "action": "试试组合因子、跨品种验证, 或开一个新主题冲榜",
        },
    },
}

MENTOR_KEEP_GOING_PREFIX: dict[Locale, str] = {
    "en": "You've completed your first full research loop! ",
    "zh": "你已经走完了第一个完整研究闭环! ",
}

DISCLAIMER: dict[Locale, str] = {
    "en": "Research workflow guidance only — not trading advice.",
    "zh": "仅为研究流程提醒, 不构成交易建议。",
}

TEMPLATE_LOCKED: dict[Locale, str] = {
    "en": "This template is locked — level up or upgrade membership.",
    "zh": "该模板尚未解锁，请升级等级或会员",
}

TEMPLATE_NOT_FOUND: dict[Locale, str] = {
    "en": "Template not found",
    "zh": "模板不存在",
}


def t(locale: Locale, table: dict[Locale, str]) -> str:
    return table.get(locale) or table["en"]


def localize_research_template(code: str, locale: Locale, fallback: dict | None = None) -> dict:
    pack = RESEARCH_TEMPLATES.get(code, {}).get(locale) or RESEARCH_TEMPLATES.get(code, {}).get("en")
    if pack:
        return dict(pack)
    if fallback:
        return {
            "title": fallback.get("title", code),
            "hypothesis": fallback.get("hypothesis", ""),
            "description": fallback.get("description", ""),
            "tags": list(fallback.get("tags") or []),
        }
    return {"title": code, "hypothesis": "", "description": "", "tags": []}


def format_lock_hint(locale: Locale, min_level: int, min_tier: int, level_ok: bool, tier_ok: bool) -> str | None:
    if level_ok and tier_ok:
        return None
    parts: list[str] = []
    if not level_ok:
        parts.append(f"L{min_level}+" if locale == "en" else f"需要 L{min_level}+")
    if not tier_ok:
        parts.append("membership" if locale == "en" else "需要会员")
    return " & ".join(parts) if locale == "en" else "、".join(parts)


LEVEL_LABELS: dict[Locale, list[str]] = {
    "en": ["Observer", "Apprentice", "Researcher", "Senior", "Quant Pro"],
    "zh": ["观察员", "研究学徒", "研究员", "进阶研究员", "量化研究员"],
}

CHALLENGE_CONTENT: dict[str, dict[Locale, dict[str, str]]] = {
    "30d-research": {
        "en": {
            "title": "30-Day Research Challenge",
            "description": "From your first factor to your first report — complete a quant study in 30 days.",
        },
        "zh": {
            "title": "30 天研究挑战",
            "description": "从第一个因子到第一份研究报告, 30 天完成你的第一个量化研究项目。",
        },
    },
}

MILESTONE_TITLES: dict[str, dict[Locale, str]] = {
    "first_factor": {
        "en": "Create your first factor",
        "zh": "创建第一个因子",
    },
    "first_oos": {
        "en": "Complete your first validation (OOS)",
        "zh": "完成第一次科学验证 (OOS)",
    },
    "stack_factor": {
        "en": "Create your first stack factor",
        "zh": "创建第一个组合因子",
    },
    "first_report": {
        "en": "Publish your first research report",
        "zh": "产出第一份研究报告",
    },
}


def level_label(locale: Locale, level: int) -> str:
    labels = LEVEL_LABELS.get(locale) or LEVEL_LABELS["en"]
    if 0 <= level < len(labels):
        return labels[level]
    return f"L{level}"


def factor_template_label(template_type: str, locale: Locale) -> str:
    pack = FACTOR_TEMPLATES.get(template_type, {}).get(locale) or FACTOR_TEMPLATES.get(
        template_type, {}
    ).get("en")
    if pack:
        return str(pack.get("label") or template_type)
    return template_type


def overlay_project_fields(
    title: str,
    question: str,
    description: str,
    tags: list,
    locale: Locale,
) -> dict[str, object]:
    """Map legacy Chinese template projects to English when locale is en."""
    if locale == "zh":
        return {}
    for packs in RESEARCH_TEMPLATES.values():
        zh = packs["zh"]
        en = packs["en"]
        if title == zh["title"] or (question and question == zh["hypothesis"]):
            return {
                "title": en["title"],
                "question": en["hypothesis"],
                "description": en["description"],
                "tags": list(en["tags"]),
            }
    return {}


def localize_challenge(challenge, locale: Locale) -> dict:
    base = {
        "id": challenge.id,
        "code": challenge.code,
        "title": challenge.title,
        "description": challenge.description,
        "days": challenge.days,
        "milestones": list(challenge.milestones or []),
    }
    pack = CHALLENGE_CONTENT.get(challenge.code, {}).get(locale)
    if pack:
        base["title"] = pack["title"]
        base["description"] = pack["description"]
    loc_ms = []
    for m in base["milestones"]:
        m2 = dict(m)
        code = m.get("code")
        if code and code in MILESTONE_TITLES:
            m2["title"] = MILESTONE_TITLES[code][locale]
        loc_ms.append(m2)
    base["milestones"] = loc_ms
    return base


def localize_progress(progress: dict, locale: Locale) -> dict:
    out = dict(progress)
    code = out.get("code")
    pack = CHALLENGE_CONTENT.get(code or "", {}).get(locale)
    if pack:
        out["title"] = pack["title"]
    loc_ms = []
    for m in out.get("milestones") or []:
        m2 = dict(m)
        mc = m.get("code")
        if mc and mc in MILESTONE_TITLES:
            m2["title"] = MILESTONE_TITLES[mc][locale]
        loc_ms.append(m2)
    out["milestones"] = loc_ms
    return out

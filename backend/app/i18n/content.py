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
            "suitable_for": "Complete beginners · trend-first study",
        },
        "zh": {
            "title": "黄金趋势研究",
            "hypothesis": "黄金价格是否存在趋势延续性?",
            "description": "用动量因子检验黄金 (AU) 的趋势是否可被捕捉。",
            "tags": ["趋势", "贵金属"],
            "suitable_for": "完全新手 · 从趋势思路入门",
        },
    },
    "commodity-momentum": {
        "en": {
            "title": "Commodity Momentum",
            "hypothesis": "Is momentum effective on rebar (RB)?",
            "description": "Study trend inertia in commodity futures with a momentum factor.",
            "tags": ["momentum", "commodity"],
            "suitable_for": "Python users · commodity futures",
        },
        "zh": {
            "title": "商品动量研究",
            "hypothesis": "螺纹钢 (RB) 的动量效应是否有效?",
            "description": "用动量因子研究商品期货的趋势惯性。",
            "tags": ["动量", "商品"],
            "suitable_for": "有 Python 基础 · 商品期货",
        },
    },
    "vol-regime": {
        "en": {
            "title": "Volatility Regime",
            "hypothesis": "Do volatility states predict return distribution?",
            "description": "Study risk regime shifts on index futures (IF) with a volatility factor.",
            "tags": ["volatility", "index"],
            "suitable_for": "Traders · risk / regime angle",
        },
        "zh": {
            "title": "波动率研究",
            "hypothesis": "波动率状态能否预示后续收益分布?",
            "description": "用波动率因子研究股指 (IF) 的风险状态切换。",
            "tags": ["波动率", "股指"],
            "suitable_for": "有交易经验 · 风险/状态切换",
        },
    },
    "mean-reversion": {
        "en": {
            "title": "Mean Reversion",
            "hypothesis": "Do prices tend to revert after deviating from the mean?",
            "description": "Test mean-reversion behavior with a dedicated factor.",
            "tags": ["mean reversion"],
            "suitable_for": "Beginners · contrarian / reversion logic",
        },
        "zh": {
            "title": "均值回归研究",
            "hypothesis": "价格偏离均值后是否倾向回归?",
            "description": "用均值回归因子检验价格的回归特性。",
            "tags": ["均值回归"],
            "suitable_for": "新手 · 逆势/回归思路",
        },
    },
    "rsi-study": {
        "en": {
            "title": "RSI Strength Study",
            "hypothesis": "Do RSI extremes contain reversal signals?",
            "description": "Study short-term strength swings on rebar with RSI.",
            "tags": ["RSI", "commodity"],
            "suitable_for": "Beginners · oscillator / overbought-oversold",
        },
        "zh": {
            "title": "RSI 强弱研究",
            "hypothesis": "RSI 超买超卖区域是否蕴含反转信号?",
            "description": "用 RSI 因子研究螺纹钢短期强弱切换。",
            "tags": ["RSI", "商品"],
            "suitable_for": "新手 · 强弱/超买超卖",
        },
    },
    "sma-cross": {
        "en": {
            "title": "SMA Deviation Study",
            "hypothesis": "Is there a tradable signal when price deviates from its moving average?",
            "description": "Study index pricing deviation with an SMA ratio factor.",
            "tags": ["moving average", "index"],
            "suitable_for": "L1+ · moving-average deviation",
        },
        "zh": {
            "title": "均线偏离研究",
            "hypothesis": "价格偏离均线后是否存在可交易信号?",
            "description": "用均线偏离因子研究股指定价偏离。",
            "tags": ["均线", "股指"],
            "suitable_for": "L1+ · 均线偏离",
        },
    },
    "multi-momentum": {
        "en": {
            "title": "Advanced Momentum",
            "hypothesis": "Is long-window momentum more robust on gold?",
            "description": "Researcher Plus — long-window momentum template.",
            "tags": ["momentum", "advanced"],
            "suitable_for": "L2 + membership · longer lookback",
        },
        "zh": {
            "title": "进阶动量组合",
            "hypothesis": "长周期动量在黄金上是否更稳健?",
            "description": "研究员会员专属 — 长窗口动量研究模板。",
            "tags": ["动量", "进阶"],
            "suitable_for": "L2 + 会员 · 长周期动量",
        },
    },
    "cost-stress-rb": {
        "en": {
            "title": "Cost Stress Test",
            "hypothesis": "Can short-window momentum survive realistic trading costs?",
            "description": "Advanced playbook — learn turnover and cost sensitivity with fast momentum.",
            "tags": ["advanced", "costs", "momentum"],
            "suitable_for": "L1+ · cost / turnover awareness",
            "learning_steps": [
                "Start with short-window momentum on RB",
                "Run parameter scan — watch turnover column",
                "Run validation — check cost sensitivity",
                "Pass quality gate before paper trading",
                "Submit a small paper order and track decay",
            ],
        },
        "zh": {
            "title": "成本压力测试",
            "hypothesis": "短周期动量能否在扣成本后仍有效?",
            "description": "进阶 Playbook — 用短窗口动量学习换手与成本敏感性。",
            "tags": ["进阶", "成本", "动量"],
            "suitable_for": "L1+ · 成本与换手意识",
            "learning_steps": [
                "短窗口动量开局（螺纹钢 RB）",
                "参数扫描 — 重点看换手率",
                "科学验证 — 打开成本敏感性",
                "通过质量闸门后再上 Paper",
                "小额 Paper 下单并开启衰减跟踪",
            ],
        },
    },
    "regime-trend-if": {
        "en": {
            "title": "Regime-Aware Trend",
            "hypothesis": "Is trend momentum more robust in low/mid volatility regimes?",
            "description": "Advanced playbook — combine vol regime context with long momentum.",
            "tags": ["advanced", "regime", "index"],
            "suitable_for": "L2 + membership · regime fit",
            "learning_steps": [
                "Long-window momentum on IF",
                "Read vol regime banner on project page",
                "Validation — check regime fit score",
                "Graduate to paper when regime fit ≥ 35",
                "Track paper NAV and decay alerts",
            ],
        },
        "zh": {
            "title": "制度感知趋势",
            "hypothesis": "在中低波动制度下趋势因子是否更稳健?",
            "description": "结合波动制度与长周期动量，学习 regime 适配。",
            "tags": ["进阶", "regime", "股指"],
            "suitable_for": "L2 + 会员 · 市况适配",
            "learning_steps": [
                "长周期动量开局（股指 IF）",
                "阅读项目页波动制度提示",
                "验证后查看 regime 适配分",
                "适配分 ≥ 35 再进 Paper",
                "跟踪 Paper 净值与衰减预警",
            ],
        },
    },
    "master-oos-gold": {
        "en": {
            "title": "Master OOS Path",
            "hypothesis": "Can SMA deviation pass strict out-of-sample tests on gold?",
            "description": "Master playbook — full path from validation to paper graduation.",
            "tags": ["master", "OOS", "precious metals"],
            "suitable_for": "L2 + Pro · full professional workflow",
            "learning_steps": [
                "SMA deviation starter on AU",
                "Backtest + full scientific validation",
                "Pass publish gate then paper graduation bar",
                "One-click paper order with factor linked",
                "Publish report when tracking stays healthy",
            ],
        },
        "zh": {
            "title": "大师级 OOS 路径",
            "hypothesis": "长周期均线偏离能否通过严格样本外检验?",
            "description": "大师 Playbook — 完整走过验证→毕业→Paper 全流程。",
            "tags": ["大师", "OOS", "贵金属"],
            "suitable_for": "L2 + 专业版 · 准职业全流程",
            "learning_steps": [
                "均线偏离开局（黄金 AU）",
                "回测 + 完整科学验证",
                "通过发布线后再冲 Paper 毕业线",
                "一键 Paper 下单（绑定因子）",
                "跟踪健康后发布研究报告",
            ],
        },
    },
    "volume-surge-rb": {
        "en": {
            "title": "Volume Surge Breakout",
            "hypothesis": "Does abnormal volume with price direction predict short-term continuation?",
            "description": "Advanced playbook — learn breakout signals with the volume surge factor.",
            "tags": ["advanced", "volume", "breakout"],
            "suitable_for": "L1+ · volume / flow awareness",
            "learning_steps": [
                "Start volume surge factor on RB (needs volume data)",
                "Backtest — watch turnover vs momentum templates",
                "Validation — compare OOS Sharpe with cost stress",
                "Check regime fit on project mastery path",
                "Paper track only after graduation bar passes",
            ],
        },
        "zh": {
            "title": "成交量异动突破",
            "hypothesis": "异常放量配合价格方向能否预测短期延续?",
            "description": "进阶 Playbook — 用成交量异动因子学习放量突破与资金流入。",
            "tags": ["进阶", "成交量", "突破"],
            "suitable_for": "L1+ · 量价/资金流意识",
            "learning_steps": [
                "成交量异动因子开局（螺纹钢 RB，需 volume 数据）",
                "回测 — 对比动量类模板的换手率",
                "科学验证 — 看样本外夏普与成本敏感性",
                "在项目大师路径查看 regime 适配分",
                "通过 Paper 毕业线后再上模拟跟踪",
            ],
        },
    },
}

LEARNING_STEPS_DEFAULT: dict[Locale, list[str]] = {
    "en": [
        "One-click start — auto project + starter factor",
        "Backtest — read Sharpe and max drawdown",
        "Scientific validation — OOS + walk-forward",
        "Generate report — publish when quality gate passes",
    ],
    "zh": [
        "一键开局 → 自动建好项目与起步因子",
        "运行回测 → 看夏普与最大回撤",
        "科学验证 → 样本外 + Walk-Forward",
        "生成报告 → 达标后发布到研究广场",
    ],
}

FACTOR_TEMPLATES: dict[str, dict[Locale, dict]] = {
    "momentum": {
        "en": {
            "label": "Momentum",
            "description": "Past N-period return; captures trend continuation.",
            "how_it_works": "Scores higher when price rose over the lookback — bets trends continue.",
            "params": {"window": "Lookback window"},
            "param_help": {
                "window": {
                    "tip": "How many bars of close price to measure past return.",
                    "low_hint": "Short window (e.g. 5–10): reacts fast, more noise.",
                    "high_hint": "Long window (60+): smoother signal, slower to turn.",
                    "suggested": "Daily research often uses 10–30 bars.",
                }
            },
        },
        "zh": {
            "label": "动量因子",
            "description": "过去 N 期收益率, 捕捉趋势延续。",
            "how_it_works": "最近涨得多 → 打分偏高，押趋势延续；跌得多 → 打分偏低。",
            "params": {"window": "回看窗口"},
            "param_help": {
                "window": {
                    "tip": "用最近多少根 K 线的收盘价，计算涨跌幅（动量）。",
                    "low_hint": "窗口偏小（如 5–10）：反应快，但容易被单日噪声干扰。",
                    "high_hint": "窗口偏大（60+）：信号更平滑，但转向更慢。",
                    "suggested": "日线研究常用 10–30；小白可先用默认 20。",
                }
            },
        },
    },
    "sma_ratio": {
        "en": {
            "label": "SMA deviation",
            "description": "Price deviation from N-period moving average.",
            "how_it_works": "Positive when price is above its moving average — relative strength vs recent average.",
            "params": {"window": "MA window"},
            "param_help": {
                "window": {
                    "tip": "Length of the simple moving average (SMA) baseline.",
                    "low_hint": "Short MA: tracks price closely, more whipsaws.",
                    "high_hint": "Long MA: stable baseline, slower mean-reversion signals.",
                    "suggested": "Try 20 on daily bars as a starting point.",
                }
            },
        },
        "zh": {
            "label": "均线偏离",
            "description": "价格相对 N 期均线的偏离度。",
            "how_it_works": "价格在均线上方 → 偏离为正；下方 → 为负。可配合趋势或回归思路使用。",
            "params": {"window": "均线窗口"},
            "param_help": {
                "window": {
                    "tip": "均线用多少根 K 线计算（简单移动平均 SMA）。",
                    "low_hint": "窗口短：均线跟价格跟得紧，信号切换更频繁。",
                    "high_hint": "窗口长：基准更稳，偏离信号更慢。",
                    "suggested": "日线可先试 20，再回测对比 10 / 60。",
                }
            },
        },
    },
    "rsi": {
        "en": {
            "label": "RSI strength",
            "description": "Relative strength index (0–100) for overbought/oversold.",
            "how_it_works": "RSI near 70+ may mean overheated; near 30− may mean oversold. Factor shifts around 50.",
            "params": {"window": "RSI window"},
            "param_help": {
                "window": {
                    "tip": "Bars used to average gains vs losses in RSI.",
                    "low_hint": "Short RSI (e.g. 7): jumps quickly, good for fast markets.",
                    "high_hint": "Long RSI (21+): smoother, fewer extreme readings.",
                    "suggested": "Classic default is 14 — a solid first try.",
                }
            },
        },
        "zh": {
            "label": "RSI 强弱",
            "description": "相对强弱指标 (0-100), 衡量超买超卖。",
            "how_it_works": "RSI 接近 70 可能偏热，接近 30 可能偏冷；因子以 50 为中轴偏移。",
            "params": {"window": "RSI 窗口"},
            "param_help": {
                "window": {
                    "tip": "计算 RSI 时，涨跌分别平均用多少根 K 线。",
                    "low_hint": "窗口短（如 7）：RSI 跳动快，适合短线实验。",
                    "high_hint": "窗口长（21+）：更平滑，极端值更少。",
                    "suggested": "经典默认 14，小白可直接用。",
                }
            },
        },
    },
    "volatility": {
        "en": {
            "label": "Volatility",
            "description": "Rolling std of returns; measures risk level.",
            "how_it_works": "High recent volatility → higher score. Often used as risk/regime filter, not pure alpha.",
            "params": {"window": "Vol window"},
            "param_help": {
                "window": {
                    "tip": "How many daily returns go into the rolling standard deviation.",
                    "low_hint": "Short window: captures recent spikes, unstable rank.",
                    "high_hint": "Long window: stable vol estimate, slow regime shifts.",
                    "suggested": "Start with 20 on daily data; validate before publishing.",
                }
            },
        },
        "zh": {
            "label": "波动率",
            "description": "收益率的滚动标准差, 衡量风险水平。",
            "how_it_works": "最近波动越大 → 打分越高。常作风险/状态过滤，单独当 alpha 要谨慎验证。",
            "params": {"window": "波动窗口"},
            "param_help": {
                "window": {
                    "tip": "用最近多少根 K 线的日收益率，算滚动标准差。",
                    "low_hint": "窗口短：对近期暴涨暴跌敏感，排名波动大。",
                    "high_hint": "窗口长：波动估计更稳，状态切换慢。",
                    "suggested": "日线可先试 20，务必做样本外验证再发布。",
                }
            },
        },
    },
    "mean_reversion": {
        "en": {
            "label": "Mean reversion",
            "description": "Negative z-score vs mean; expects reversion.",
            "how_it_works": "Price far below average → positive score (expect bounce); far above → negative.",
            "params": {"window": "Lookback window"},
            "param_help": {
                "window": {
                    "tip": "Bars for rolling mean and std when computing z-score.",
                    "low_hint": "Short window: quick mean, more false extremes.",
                    "high_hint": "Long window: slow mean, fewer reversion bets.",
                    "suggested": "20 bars on daily is a common starting point.",
                }
            },
        },
        "zh": {
            "label": "均值回归",
            "description": "价格相对均值的负向 z-score, 预期向均值回归。",
            "how_it_works": "价格远低于均线 → 打分偏高（期待反弹）；远高于均线 → 打分偏低。",
            "params": {"window": "回看窗口"},
            "param_help": {
                "window": {
                    "tip": "计算 z-score 时，均值和标准差各用多少根 K 线。",
                    "low_hint": "窗口短：均值跟得紧，极端值出现更频繁。",
                    "high_hint": "窗口长：均值更慢，回归信号更少。",
                    "suggested": "日线常用 20，调参后一定要重新验证。",
                }
            },
        },
    },
    "volume_surge": {
        "en": {
            "label": "Volume surge",
            "description": "Volume z-score × price direction; captures breakout flow.",
            "how_it_works": "High volume on up days → positive score; high volume on down days → negative. Needs OHLCV with volume.",
            "params": {"window": "Volume window"},
            "param_help": {
                "window": {
                    "tip": "Rolling window for average volume and std when detecting surges.",
                    "low_hint": "Short window (10): catches sudden spikes, more noise.",
                    "high_hint": "Long window (60+): stable baseline, misses fast breakouts.",
                    "suggested": "Start with 20 on daily RB/IF; validate turnover carefully.",
                }
            },
        },
        "zh": {
            "label": "成交量异动",
            "description": "成交量 z-score × 涨跌方向, 捕捉放量突破与资金流入。",
            "how_it_works": "上涨日放量 → 打分偏高；下跌日放量 → 打分偏低。需要带 volume 的行情数据。",
            "params": {"window": "量能窗口"},
            "param_help": {
                "window": {
                    "tip": "计算成交量均值和标准差用多少根 K 线。",
                    "low_hint": "窗口短（10 左右）：对突发放量敏感，噪声也更多。",
                    "high_hint": "窗口长（60+）：基准更稳，可能错过快速突破。",
                    "suggested": "日线 RB/IF 可先试 20，务必关注换手率与成本。",
                }
            },
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

MASTERY_STAGE_LABEL: dict[Locale, dict[str, str]] = {
    "en": {
        "start": "build factor",
        "backtest": "run backtest",
        "validate": "run validation",
        "graduate": "pass publish gate",
        "paper": "submit paper order",
        "track": "monitor paper NAV",
        "share": "publish & share",
        "revalidate": "re-validate after decay",
    },
    "zh": {
        "start": "建因子",
        "backtest": "跑回测",
        "validate": "做验证",
        "graduate": "过发布线",
        "paper": "下 Paper 单",
        "track": "跟踪 Paper",
        "share": "发布分享",
        "revalidate": "衰减后重验",
    },
}

MASTERY_GOAL_HINT: dict[Locale, dict[str, str]] = {
    "en": {
        "on_board": "You are on the Paper Masters board (#{rank}) with {count} graduated factor(s).",
        "paper_ready": "Paper bar passed — submit a paper order to climb the masters board.",
        "in_progress": "Next toward Paper Masters: {next} ({pct}% on mastery path).",
        "start": "Start a project from a template — the mastery path leads to the Paper Masters board.",
        "outside_board_graduated": "Top {limit}: #{limit} needs {cutoff} graduated factor(s). You have {count} — {needed} more to reach the line.",
        "outside_board_tracking": "You match the graduation bar ({count}) — track more paper NAV to climb past rank #{limit}.",
        "outside_board_rank": "You rank #{rank} globally — {outside} spots outside the top {limit}.",
    },
    "zh": {
        "on_board": "你已在 Paper 大师榜第 {rank} 名（{count} 个毕业因子）。",
        "paper_ready": "已通过 Paper 毕业线 — 下模拟单即可冲击大师榜。",
        "in_progress": "距 Paper 大师榜：下一步 {next}（大师路径 {pct}%）。",
        "start": "从模板开局 — 跟着大师路径就能冲上 Paper 大师榜。",
        "outside_board_graduated": "前 {limit} 名入榜线约 {cutoff} 个毕业因子，你已有 {count} 个 — 还差 {needed} 个。",
        "outside_board_tracking": "毕业数已达入榜线（{count} 个）— 多跟踪 Paper 净值即可往前冲。",
        "outside_board_rank": "你当前全站第 {rank} 名 — 距前 {limit} 名还差 {outside} 位。",
    },
}

REGIME_LABEL: dict[Locale, dict[str, str]] = {
    "en": {"low": "Low volatility", "mid": "Mid volatility", "high": "High volatility"},
    "zh": {"low": "低波动", "mid": "中等波动", "high": "高波动"},
}

REGIME_COACH: dict[Locale, dict[str, str]] = {
    "en": {
        "high": "High-vol regime — mean-reversion / RSI templates often fit better; trend plays need tighter risk control.",
        "low": "Low-vol regime — momentum may lag; volatility or patience for regime shifts can help.",
        "mid": "Mid-vol regime — most starter templates are fair game; still run OOS validation.",
        "unavailable": "Market data not ready — pick any beginner template to start your mastery path.",
    },
    "zh": {
        "high": "高波动制度 — 均值回归 / RSI 类模板往往更合拍；趋势策略注意回撤与成本。",
        "low": "低波动制度 — 突破动量信号偏弱，可关注波动率模板或等待制度切换。",
        "mid": "中等波动 — 大部分入门模板都值得一试，仍建议做样本外验证。",
        "unavailable": "行情数据暂不可用 — 任选入门模板即可开始大师路径。",
    },
}

FIT_VERDICT_LABEL: dict[Locale, dict[str, str]] = {
    "en": {"适合": "Good fit", "一般": "Moderate", "谨慎": "Caution"},
    "zh": {"适合": "适合", "一般": "一般", "谨慎": "谨慎"},
}

STRATEGY_STYLE_LABEL: dict[Locale, dict[str, str]] = {
    "en": {
        "trend": "Trend/momentum",
        "mean_reversion": "Mean reversion",
        "volatility": "Volatility",
        "generic": "General",
    },
    "zh": {
        "trend": "趋势/动量",
        "mean_reversion": "均值回归",
        "volatility": "波动率",
        "generic": "综合",
    },
}

REGIME_NEXT_ACTION: dict[Locale, str] = {
    "en": " · {regime} regime → recommended 「{title}」 ({verdict} {score})",
    "zh": " · 当前{regime}，推荐「{title}」（{verdict} {score}分）",
}

ATTENTION_ALERT: dict[Locale, dict[str, str]] = {
    "en": {
        "regime_shift_title": "Regime shift · {symbol}",
        "regime_shift_msg": "{from_label} → {to_label} on 「{project_title}」 — re-validate factor fit.",
        "weak_fit_title": "Weak regime fit · {symbol}",
        "weak_fit_msg": "「{project_title}」 scores {score} ({verdict}) — try a better-matched template.",
        "paper_decay_watch_title": "Paper drift · {factor_name}",
        "paper_decay_alert_title": "Paper decay alert · {factor_name}",
        "paper_decay_msg": "Paper NAV diverges from validation — review or re-validate.",
        "paper_factor_fallback": "your factor",
    },
    "zh": {
        "regime_shift_title": "制度切换 · {symbol}",
        "regime_shift_msg": "「{project_title}」：{from_label} → {to_label}，建议重验因子适配。",
        "weak_fit_title": "制度适配偏弱 · {symbol}",
        "weak_fit_msg": "「{project_title}」适配 {score} 分（{verdict}）— 可换更合拍的模板。",
        "paper_decay_watch_title": "Paper 走弱 · {factor_name}",
        "paper_decay_alert_title": "Paper 衰减预警 · {factor_name}",
        "paper_decay_msg": "纸面净值与验证期偏离 — 建议复查或重验。",
        "paper_factor_fallback": "你的因子",
    },
}

JOINT_ATTENTION_COACH: dict[Locale, dict[str, dict[str, str]]] = {
    "en": {
        "shift_decay": {
            "title": "Double risk · {symbol}",
            "tip": "Regime shifted ({from_label} → {to_label}) while paper is {decay_status}. Re-validate or switch to a regime-matched template before tracking further.",
            "action": "revalidate",
        },
        "shift_weak_fit": {
            "title": "Regime shift + weak fit · {symbol}",
            "tip": "Market moved to {to_label} and your factor scores {fit_score} ({fit_verdict}). Pick a better-matched template, then re-run OOS validation.",
            "action": "templates",
        },
        "shift_only": {
            "title": "Regime shift · {symbol}",
            "tip": "Volatility regime changed ({from_label} → {to_label}). Re-check factor fit and run a fresh validation pass.",
            "action": "revalidate",
        },
        "weak_decay": {
            "title": "Weak fit + paper drift · {symbol}",
            "tip": "Factor fit is {fit_score} ({fit_verdict}) and paper is {decay_status}. Consider a regime-aligned template and re-validate.",
            "action": "templates",
        },
    },
    "zh": {
        "shift_decay": {
            "title": "双重风险 · {symbol}",
            "tip": "制度已切换（{from_label} → {to_label}）且 Paper 呈 {decay_status} 态。继续跟踪前请先重验，或换更合拍的制度模板。",
            "action": "revalidate",
        },
        "shift_weak_fit": {
            "title": "制度切换 + 弱适配 · {symbol}",
            "tip": "市况变为 {to_label}，当前因子仅 {fit_score} 分（{fit_verdict}）。建议换制度推荐模板后重跑样本外验证。",
            "action": "templates",
        },
        "shift_only": {
            "title": "制度切换 · {symbol}",
            "tip": "波动制度变化（{from_label} → {to_label}）。请复查因子适配并补跑一次验证。",
            "action": "revalidate",
        },
        "weak_decay": {
            "title": "弱适配 + Paper 走弱 · {symbol}",
            "tip": "适配 {fit_score} 分（{fit_verdict}）且 Paper 呈 {decay_status} 态。建议换制度合拍模板后重验。",
            "action": "templates",
        },
    },
}

MENTOR_ATTENTION_APPEND: dict[Locale, str] = {
    "en": " · Needs attention: {summary}",
    "zh": " · 另需关注：{summary}",
}

ALERT_CHALLENGE_HINT: dict[Locale, dict[str, str]] = {
    "en": {
        "regime_shift_d22": "30-day challenge D22 — re-validate fit, then submit your first paper order.",
        "weak_fit_d22": "30-day challenge D22 — pick a regime-matched template before paper order.",
        "paper_decay_d28": "30-day challenge D28 — fix paper drift to pass the graduation gate.",
        "regime_shift_d28": "30-day challenge D28 — regime shifted; re-validate to graduate.",
    },
    "zh": {
        "regime_shift_d22": "30 天挑战 D22 — 重验适配后下第一笔 Paper 单即可点亮里程碑。",
        "weak_fit_d22": "30 天挑战 D22 — 换更合拍模板，达标后再下 Paper 单。",
        "paper_decay_d28": "30 天挑战 D28 — 处理 Paper 衰减，通过毕业线即可点亮。",
        "regime_shift_d28": "30 天挑战 D28 — 制度切换，重验通过即可毕业。",
    },
}

CHALLENGE_PAPER_COACH: dict[Locale, dict[str, str]] = {
    "en": {
        "d22_ready": "Challenge D{day}: 「{title}」 — paper bar passed. Submit a paper order on your project to light this milestone.",
        "d22_not_ready": "Challenge D{day}: 「{title}」 — optimize to the paper graduation line first, then submit your order.",
        "d22_with_attention": "Challenge D{day}: 「{title}」 — {attention_count} alert(s) need action before paper order. Fix fit or decay, then submit.",
        "d28_ready": "Challenge D{day}: 「{title}」 — you're close. Confirm paper tracking meets the graduation gate.",
        "d28_not_ready": "Challenge D{day}: 「{title}」 — push your factor through the paper quality gate.",
        "d28_decay": "Challenge D{day}: 「{title}」 — paper decay alert active. Re-validate, then pass graduation to complete D28.",
    },
    "zh": {
        "d22_ready": "挑战 D{day}：「{title}」— 已过 Paper 毕业线，去项目页下模拟单即可点亮。",
        "d22_not_ready": "挑战 D{day}：「{title}」— 先优化到 Paper 毕业线，再下模拟单。",
        "d22_with_attention": "挑战 D{day}：「{title}」— 有 {attention_count} 条提醒待处理，修好适配/衰减后再下单。",
        "d28_ready": "挑战 D{day}：「{title}」— 即将毕业，确认 Paper 跟踪达到毕业线。",
        "d28_not_ready": "挑战 D{day}：「{title}」— 把因子推过 Paper 质量闸门。",
        "d28_decay": "挑战 D{day}：「{title}」— Paper 衰减提醒中，重验通过毕业线即可点亮 D28。",
    },
}

JOURNEY_STEPS: dict[Locale, dict[str, str]] = {
    "en": {
        "template": "Pick template",
        "factor": "Create factor",
        "backtest": "Backtest",
        "validation": "Validate",
        "report": "Report",
        "publish": "Publish",
        "share": "Share card",
    },
    "zh": {
        "template": "选模板",
        "factor": "建因子",
        "backtest": "回测",
        "validation": "验证",
        "report": "报告",
        "publish": "发布",
        "share": "分享",
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
    "run_paper": {
        "en": {
            "title": "Submit your first paper order",
            "action": "You passed the paper graduation bar — link your factor and start live tracking",
        },
        "zh": {
            "title": "提交第一笔 Paper 模拟单",
            "action": "已通过 Paper 毕业线 — 绑定因子下单，开启真实跟踪",
        },
    },
    "revalidate_decay": {
        "en": {
            "title": "Paper decay detected — back to the lab",
            "action": "Paper metrics diverged from validation. Tweak your factor and re-run OOS before continuing.",
        },
        "zh": {
            "title": "纸面衰减告警 — 回实验室复查",
            "action": "模拟盘表现偏离验证期基准。请调参并重新跑样本外验证，再继续跟踪。",
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

MENTOR_REGIME_APPEND: dict[Locale, str] = {
    "en": " {symbol} is in {regime} — {coach} Try 「{title}」 ({verdict} {score}).",
    "zh": " {symbol} 当前{regime} — {coach} 建议从「{title}」开局（{verdict} {score}分）。",
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
        out = dict(pack)
    elif fallback:
        out = {
            "title": fallback.get("title", code),
            "hypothesis": fallback.get("hypothesis", ""),
            "description": fallback.get("description", ""),
            "tags": list(fallback.get("tags") or []),
        }
    else:
        out = {"title": code, "hypothesis": "", "description": "", "tags": []}
    out.setdefault("suitable_for", "")
    out.setdefault("learning_steps", LEARNING_STEPS_DEFAULT.get(locale) or LEARNING_STEPS_DEFAULT["en"])
    return out


def template_teaching_bundle(
    code: str,
    factor_template: str,
    default_params: dict | None,
    locale: Locale,
) -> dict:
    """研究模板卡片教学信息 (因子说明 + 学习路径)。"""
    loc = localize_research_template(code, locale)
    ft = FACTOR_TEMPLATES.get(factor_template, {}).get(locale) or FACTOR_TEMPLATES.get(factor_template, {}).get("en") or {}
    params = default_params or {}
    param_bits: list[str] = []
    for key, val in params.items():
        ph = (ft.get("param_help") or {}).get(key) or {}
        hint = ph.get("suggested") or ph.get("tip") or key
        param_bits.append(f"{key}={val}")
    params_line = ", ".join(param_bits)
    label = ft.get("label", factor_template)
    if locale == "zh":
        factor_note = f"内置「{label}」因子，默认 {params_line}"
    else:
        factor_note = f"Starter factor: {label} ({params_line})"
    return {
        "suitable_for": loc.get("suitable_for", ""),
        "learning_steps": loc.get("learning_steps") or LEARNING_STEPS_DEFAULT.get(locale) or LEARNING_STEPS_DEFAULT["en"],
        "factor_template_label": label,
        "factor_note": factor_note,
        "how_it_works": ft.get("how_it_works", ""),
    }


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

# 挑战里程碑 ↔ 七步研究闭环 (journey step key)
MILESTONE_JOURNEY_KEYS: dict[str, str] = {
    "first_factor": "factor",
    "first_oos": "validation",
    "stack_factor": "factor",
    "first_paper_order": "publish",
    "paper_graduated": "publish",
    "first_report": "report",
}

MILESTONE_MASTERY_STAGES: dict[str, str] = {
    "first_paper_order": "paper",
    "paper_graduated": "graduate",
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
    "first_paper_order": {
        "en": "Submit your first paper order",
        "zh": "下第一笔 Paper 模拟单",
    },
    "paper_graduated": {
        "en": "Pass the paper quality gate",
        "zh": "因子通过 Paper 毕业线",
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
        jk = m.get("journey_key") or (MILESTONE_JOURNEY_KEYS.get(mc or "") if mc else None)
        if jk:
            m2["journey_key"] = jk
            labels = JOURNEY_STEPS.get(locale) or JOURNEY_STEPS["en"]
            m2["journey_label"] = labels.get(jk, jk)
        ms = m.get("mastery_stage") or MILESTONE_MASTERY_STAGES.get(mc or "")
        if ms:
            m2["mastery_stage"] = ms
            stage_labels = MASTERY_STAGE_LABEL.get(locale) or MASTERY_STAGE_LABEL["en"]
            m2["mastery_stage_label"] = stage_labels.get(ms, ms)
        loc_ms.append(m2)
    out["milestones"] = loc_ms
    return out

# AI Strategy Builder

## Flow

```text
Natural Language (中文)
 → Intent Parser (rule-based v1)
 → Strategy Spec Draft
 → Ambiguity Detector
 → Structured Confirmation
 → Schema Validation
 → Spec Compiler
 → Nautilus Backtest (research only)
 → Chinese Report
```

## Hard rules

```text
AI_CAN_RECOMMEND = YES
AI_CAN_GENERATE_DRAFT = YES
AI_CAN_RUN_RESEARCH = YES
AI_CAN_RUN_BACKTEST = YES
AI_CAN_BYPASS_GATE = NO
AI_CAN_APPROVE_LIVE = NO
```

Ambiguous ideas (e.g.「黄金突破就买」) must ask clarifying questions.  
Assumed values are labeled `ASSUMED_VALUE` / `assumed_values[]`.

## API

`POST /api/v1/ai/strategy-builder`

```json
{"text": "欧元美元15分钟 EMA10上穿EMA20", "confirm": true, "run_backtest": true}
```

Enabled when `QUANTLAB_AI_STRATEGY_BUILDER` / `QUANTLAB_NAUTILUS_ENGINE` or `APP_ENV=development|test`.

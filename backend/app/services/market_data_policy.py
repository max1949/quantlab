"""行情数据访问策略 — 按会员档位限制周期与历史深度。

免费: 仅日线, 近 1 年 (~252 根)
研究员: 日线 2 年 + 分钟线 1 年 (最多 5 万根)
专业: 全历史
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.market import DataSnapshot, MarketDataset
from backend.app.models.user import User
from backend.app.services import market_data, membership_service as ms

TIER_MARKET_POLICY: dict[int, dict] = {
    0: {
        "timeframes": frozenset({"1d"}),
        "max_bars": {"1d": 252},
        "summary_zh": "免费: 日线 · 近1年",
        "summary_en": "Free: daily · last 1 year",
        "limit_labels": {"1d": "近1年 (252根)"},
    },
    1: {
        "timeframes": frozenset({"1d", "1m", "5m", "15m"}),
        "max_bars": {"1d": 504, "1m": 50_000, "5m": 20_000, "15m": 10_000},
        "summary_zh": "研究员: 日线2年 / 5m·15m·1m 分钟级",
        "summary_en": "Researcher: 2y daily / 5m·15m·1m intraday",
        "limit_labels": {
            "1d": "近2年 (504根)",
            "1m": "近1年 (5万根)",
            "5m": "近2万根",
            "15m": "近1万根",
        },
    },
    2: {
        "timeframes": frozenset({"1d", "1m", "5m", "15m", "30m", "1h"}),
        "max_bars": {"1d": None, "1m": None, "5m": None, "15m": None, "30m": None, "1h": None},
        "summary_zh": "专业: 全历史 · 含 30m/1h",
        "summary_en": "Pro: full history incl. 30m/1h",
        "limit_labels": {
            "1d": "全历史",
            "1m": "全历史",
            "5m": "全历史",
            "15m": "全历史",
            "30m": "全历史",
            "1h": "全历史",
        },
    },
}


class MarketDataAccessError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def policy_for_tier(tier: int) -> dict:
    return TIER_MARKET_POLICY.get(tier, TIER_MARKET_POLICY[0])


def allowed_timeframes(tier: int) -> list[str]:
    return sorted(policy_for_tier(tier)["timeframes"])


def max_bars_for(tier: int, timeframe: str) -> int | None:
    return policy_for_tier(tier)["max_bars"].get(timeframe)


def trim_ohlcv(df, cap: int | None):
    if cap is None or len(df) <= cap:
        return df
    return df.iloc[-int(cap):].copy()


def assert_timeframe_allowed(db: Session, user: User, timeframe: str) -> None:
    tier = ms.current_tier(db, user)
    if timeframe not in policy_for_tier(tier)["timeframes"]:
        name = ms.TIER_NAMES.get(tier, "免费")
        raise MarketDataAccessError(
            f"当前套餐（{name}）不支持 {timeframe} 周期。"
            f"免费版仅可用日线；分钟线需研究员月卡及以上。"
        )


def load_for_user(db: Session, user: User, symbol: str, timeframe: str = "1d"):
    assert_timeframe_allowed(db, user, timeframe)
    tier = ms.current_tier(db, user)
    cap = max_bars_for(tier, timeframe)
    return market_data.load_ohlcv(symbol, timeframe, max_rows=cap)


def load_for_snapshot(
    db: Session, user: User, symbol: str, snap: DataSnapshot | None
):
    tf = snap.timeframe if snap else "1d"
    df = load_for_user(db, user, symbol, tf)
    return market_data.slice_to_snapshot(df, snap)


def effective_rows(total_rows: int, tier: int, timeframe: str) -> int:
    cap = max_bars_for(tier, timeframe)
    if cap is None:
        return total_rows
    return min(total_rows, cap)


def list_datasets_for_user(db: Session, user: User) -> list[dict]:
    tier = ms.current_tier(db, user)
    policy = policy_for_tier(tier)
    out: list[dict] = []
    for ds in market_data.list_datasets(db):
        if ds.timeframe not in policy["timeframes"]:
            continue
        eff = effective_rows(ds.rows, tier, ds.timeframe)
        out.append(
            {
                "symbol": ds.symbol,
                "timeframe": ds.timeframe,
                "start_date": ds.start_date,
                "end_date": ds.end_date,
                "rows": ds.rows,
                "effective_rows": eff,
                "tier_cap": max_bars_for(tier, ds.timeframe),
            }
        )
    return out


def entitlement_payload(db: Session, user: User, locale: str = "zh") -> dict:
    tier = ms.current_tier(db, user)
    policy = policy_for_tier(tier)
    loc = "en" if locale == "en" else "zh"
    limits = {}
    labels = policy.get("limit_labels", {})
    for tf in sorted(policy["timeframes"]):
        cap = policy["max_bars"].get(tf)
        limits[tf] = {
            "max_bars": cap,
            "label": labels.get(tf) or ("全历史" if cap is None else f"近{cap}根"),
        }
    return {
        "allowed_timeframes": sorted(policy["timeframes"]),
        "limits": limits,
        "summary": policy[f"summary_{loc}"],
        "tier": tier,
    }


def market_data_coaching_payload(
    db: Session,
    user: User,
    locale: str = "zh",
    *,
    symbol: str | None = None,
    has_active_research: bool = False,
) -> dict | None:
    """行情深度 × 数据质量 — 友好升级引导 (大师路径需更长样本外)。"""
    from backend.app.core.locale import Locale
    from backend.app.i18n import content as i18n
    from backend.app.services import payment_service
    from engine.data_quality import assess_ohlcv_quality

    if not has_active_research:
        return None

    loc: Locale = "zh" if locale == "zh" else "en"
    tier = ms.current_tier(db, user)
    if tier >= ms.TIER_PRO:
        return None

    sym = (symbol or "RB").upper()
    ds_row = None
    for row in list_datasets_for_user(db, user):
        if row["symbol"] == sym and row["timeframe"] == "1d":
            ds_row = row
            break

    capped = bool(
        ds_row
        and ds_row.get("tier_cap")
        and ds_row["effective_rows"] < ds_row["rows"]
    )

    quality_poor = False
    qual: dict = {}
    try:
        df = load_for_user(db, user, sym, "1d")
        qual = assess_ohlcv_quality(df, "1d")
        quality_poor = not qual.get("passed", True)
    except MarketDataAccessError:
        pass

    reason: str | None = None
    if tier == ms.TIER_FREE:
        if capped:
            reason = "free_history_cap"
        elif quality_poor:
            reason = "free_quality"
        elif has_active_research:
            reason = "free_upgrade_hint"
    elif tier == ms.TIER_PLUS:
        if capped:
            reason = "plus_history_cap"
        elif quality_poor:
            reason = "plus_quality"

    if not reason:
        return None

    if reason in ("plus_history_cap", "plus_quality"):
        plan_code = "pro_monthly"
        target_tier = ms.TIER_PRO
    else:
        plan_code = "plus_monthly"
        target_tier = ms.TIER_PLUS

    plan = ms.PLAN_BY_CODE[plan_code]
    labels = i18n.DATA_COACH.get(loc) or i18n.DATA_COACH["en"]
    cur_policy = policy_for_tier(tier)
    tgt_policy = policy_for_tier(target_tier)

    return {
        "symbol": sym,
        "timeframe": "1d",
        "current_tier": tier,
        "current_summary": cur_policy[f"summary_{loc}"],
        "target_tier": target_tier,
        "target_summary": tgt_policy[f"summary_{loc}"],
        "plan_code": plan_code,
        "plan_name": plan["name"],
        "price_cny": plan["price_cny"],
        "reason": reason,
        "message": labels[reason].format(
            symbol=sym,
            effective=ds_row["effective_rows"] if ds_row else 0,
            total=ds_row["rows"] if ds_row else 0,
            grade=qual.get("grade", ""),
        ),
        "effective_rows": ds_row["effective_rows"] if ds_row else None,
        "total_rows": ds_row["rows"] if ds_row else None,
        "quality_grade": qual.get("grade"),
        "quality_warnings": (qual.get("warnings") or [])[:2],
        "cta_path": "/pricing",
        "stripe_available": payment_service.stripe_configured(),
    }

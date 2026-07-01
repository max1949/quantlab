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
    },
    1: {
        "timeframes": frozenset({"1d", "1m"}),
        "max_bars": {"1d": 504, "1m": 50_000},
        "summary_zh": "研究员: 日线2年 / 分钟线1年",
        "summary_en": "Researcher: 2y daily / 1y 1-minute",
    },
    2: {
        "timeframes": frozenset({"1d", "1m"}),
        "max_bars": {"1d": None, "1m": None},
        "summary_zh": "专业: 全历史行情",
        "summary_en": "Pro: full history",
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
    df = market_data.load_ohlcv(symbol, timeframe)
    return trim_ohlcv(df, cap)


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


def entitlement_payload(db: Session, user: User) -> dict:
    tier = ms.current_tier(db, user)
    policy = policy_for_tier(tier)
    limits = {}
    for tf in sorted(policy["timeframes"]):
        cap = policy["max_bars"].get(tf)
        limits[tf] = {
            "max_bars": cap,
            "label": f"近{cap}根" if cap else "全历史",
        }
    return {
        "allowed_timeframes": sorted(policy["timeframes"]),
        "limits": limits,
        "summary": policy["summary_zh"],
    }

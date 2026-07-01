"""行情数据服务 (Sprint 4): Parquet 读写 + 索引登记 + 数据快照。

V1: PostgreSQL 存索引 (MarketDataset) + Parquet 存 K 线。
没有真实行情源时, 用确定性生成器产出样本 OHLCV (按品种派生随机种子),
保证"可复现"。真实数据接入后, 只需替换 generate/ingest 部分。
"""

from __future__ import annotations

import datetime as _dt
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.market import DataSnapshot, MarketDataset

settings = get_settings()

DEFAULT_SYMBOLS = ["RB", "AU", "IF"]

# 业务品种 -> 新浪连续主力合约代码 (akshare futures_main_sina)
FUTURES_MAIN_CODE = {"RB": "RB0", "AU": "AU0", "IF": "IF0"}


def market_dir() -> Path:
    p = Path(settings.market_data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def dataset_path(symbol: str, timeframe: str = "1d") -> Path:
    return market_dir() / f"{symbol}_{timeframe}.parquet"


def _symbol_seed(symbol: str) -> int:
    return int(hashlib.sha256(symbol.encode()).hexdigest(), 16) % (2**32)


def generate_sample_ohlcv(symbol: str, n: int = 504, start: float = 100.0) -> pd.DataFrame:
    """确定性样本 OHLCV (按品种派生种子, 不同品种走势不同)。"""
    rng = np.random.default_rng(_symbol_seed(symbol))
    rets = rng.normal(loc=0.0003, scale=0.018, size=n)
    close = start * np.cumprod(1.0 + rets)
    index = pd.date_range("2023-01-02", periods=n, freq="B")
    # 由 close 反推合理的 OHLC
    daily_range = np.abs(rng.normal(0.0, 0.01, size=n)) * close
    open_ = np.concatenate([[start], close[:-1]])
    high = np.maximum(open_, close) + daily_range
    low = np.minimum(open_, close) - daily_range
    volume = rng.integers(1_000, 50_000, size=n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


def fetch_real_ohlcv(
    symbol: str, start: str = "20180101", end: str | None = None
) -> pd.DataFrame:
    """从 akshare 拉取真实日线行情 (连续主力合约)。

    返回与样本数据同构的 DataFrame: index=DatetimeIndex,
    列 = [open, high, low, close, volume]。按列位置取值, 规避中文列名编码问题。
    """
    import akshare as ak  # 延迟导入: 没装/离线时不影响其它功能

    code = FUTURES_MAIN_CODE.get(symbol, f"{symbol}0")
    end = end or _dt.date.today().strftime("%Y%m%d")
    raw = ak.futures_main_sina(symbol=code, start_date=start, end_date=end)
    if raw is None or len(raw) == 0:
        raise ValueError(f"真实行情为空: {symbol} ({code})")

    cols = list(raw.columns)  # 顺序: 日期,开盘,最高,最低,收盘,成交量,持仓量,结算价
    df = pd.DataFrame(
        {
            "open": pd.to_numeric(raw[cols[1]], errors="coerce"),
            "high": pd.to_numeric(raw[cols[2]], errors="coerce"),
            "low": pd.to_numeric(raw[cols[3]], errors="coerce"),
            "close": pd.to_numeric(raw[cols[4]], errors="coerce"),
            "volume": pd.to_numeric(raw[cols[5]], errors="coerce"),
        }
    )
    df.index = pd.to_datetime(raw[cols[0]])
    df = df.dropna(subset=["close"]).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if df.empty:
        raise ValueError(f"真实行情清洗后无有效行: {symbol}")
    return df


def load_ohlcv(symbol: str, timeframe: str = "1d") -> pd.DataFrame:
    path = dataset_path(symbol, timeframe)
    if not path.exists():
        raise FileNotFoundError(f"行情数据不存在: {symbol} ({path})")
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    return df


def slice_to_snapshot(df: pd.DataFrame, snap: DataSnapshot | None) -> pd.DataFrame:
    """按数据快照的日期区间切片 (回测/验证执行时与创建时一致)。"""
    if snap is None or df.empty:
        return df
    start = pd.Timestamp(snap.start_date)
    end = pd.Timestamp(snap.end_date)
    if hasattr(df.index, "normalize"):
        try:
            if df.index.max().hour != 0 or df.index.min().hour != 0:
                end = end + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        except (TypeError, ValueError):
            pass
    out = df.loc[(df.index >= start) & (df.index <= end)]
    if snap.rows and len(out) > snap.rows:
        out = out.iloc[-snap.rows :]
    return out


def register_dataset(
    db: Session, symbol: str, df: pd.DataFrame, timeframe: str = "1d"
) -> MarketDataset:
    """登记/更新行情索引。"""
    path = dataset_path(symbol, timeframe)
    existing = db.execute(
        select(MarketDataset).where(
            MarketDataset.symbol == symbol, MarketDataset.timeframe == timeframe
        )
    ).scalar_one_or_none()

    start_d = df.index.min().date()
    end_d = df.index.max().date()
    if existing is None:
        existing = MarketDataset(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_d,
            end_date=end_d,
            rows=int(df.shape[0]),
            path=str(path),
        )
        db.add(existing)
    else:
        existing.start_date = start_d
        existing.end_date = end_d
        existing.rows = int(df.shape[0])
        existing.path = str(path)
    db.commit()
    db.refresh(existing)
    return existing


def list_datasets(db: Session) -> list[MarketDataset]:
    return list(
        db.execute(select(MarketDataset).order_by(MarketDataset.symbol)).scalars().all()
    )


def get_dataset(db: Session, symbol: str, timeframe: str = "1d") -> MarketDataset | None:
    return db.execute(
        select(MarketDataset).where(
            MarketDataset.symbol == symbol, MarketDataset.timeframe == timeframe
        )
    ).scalar_one_or_none()


def seed_sample_market_data(db: Session, symbols: list[str] | None = None) -> dict:
    """生成并登记样本行情 (幂等: 覆盖写 Parquet + upsert 索引)。"""
    symbols = symbols or DEFAULT_SYMBOLS
    out = []
    for sym in symbols:
        df = generate_sample_ohlcv(sym)
        df.to_parquet(dataset_path(sym))
        ds = register_dataset(db, sym, df)
        out.append({"symbol": sym, "rows": ds.rows})
    return {"datasets": out, "dir": str(market_dir())}


def seed_real_market_data(
    db: Session, symbols: list[str] | None = None, fallback: bool = True
) -> dict:
    """拉取真实行情并登记 (幂等: 覆盖写 Parquet + upsert 索引)。

    每个品种优先用真实数据; 拉取失败时, 若 fallback=True 则退回确定性样本数据,
    保证系统永远有可用行情 (离线也能跑)。
    """
    symbols = symbols or DEFAULT_SYMBOLS
    out = []
    for sym in symbols:
        path = dataset_path(sym, "1d")
        if path.exists():
            df = load_ohlcv(sym, "1d")
            ds = register_dataset(db, sym, df, "1d")
            out.append(
                {
                    "symbol": sym,
                    "rows": ds.rows,
                    "source": "local_parquet",
                    "start": str(ds.start_date),
                    "end": str(ds.end_date),
                }
            )
            continue
        source = "real"
        try:
            df = fetch_real_ohlcv(sym)
        except Exception as exc:  # 网络/数据源异常 -> 样本兜底
            if not fallback:
                raise
            source = f"sample(fallback:{type(exc).__name__})"
            df = generate_sample_ohlcv(sym)
        df.to_parquet(dataset_path(sym))
        ds = register_dataset(db, sym, df)
        out.append(
            {
                "symbol": sym,
                "rows": ds.rows,
                "source": source,
                "start": str(ds.start_date),
                "end": str(ds.end_date),
            }
        )
    return {"datasets": out, "dir": str(market_dir())}


def import_vnpy_sqlite(
    db: Session,
    sqlite_path: str | Path,
    *,
    symbol: str | None = None,
    interval: str = "1m",
    timeframe: str | None = None,
    exchange: str | None = None,
) -> dict:
    """从 vn.py 本地 SQLite (dbbardata) 导入 K 线到 Parquet + 索引。

    symbol: 输出品种名 (默认用库内 symbol); timeframe: 输出周期标签 (默认与 interval 相同)。
    """
    import sqlite3

    path = Path(sqlite_path)
    if not path.is_file():
        raise FileNotFoundError(f"vn.py 数据库不存在: {path}")

    conn = sqlite3.connect(str(path))
    try:
        q = "SELECT symbol, exchange, datetime, interval, volume, open_interest, open_price, high_price, low_price, close_price FROM dbbardata"
        clauses: list[str] = []
        params: list[str] = []
        if symbol:
            clauses.append("symbol = ?")
            params.append(symbol)
        if exchange:
            clauses.append("exchange = ?")
            params.append(exchange)
        if interval:
            clauses.append("interval = ?")
            params.append(interval)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY datetime"
        raw = pd.read_sql(q, conn, params=params)
    finally:
        conn.close()

    if raw.empty:
        raise ValueError("vn.py 数据库中没有匹配的 K 线")

    out_symbol = symbol or str(raw.iloc[0]["symbol"])
    out_tf = timeframe or interval
    raw["datetime"] = pd.to_datetime(raw["datetime"], errors="coerce")
    raw = raw.dropna(subset=["datetime"])
    if raw.empty:
        raise ValueError("vn.py 数据 datetime 无法解析")

    df = pd.DataFrame(
        {
            "open": pd.to_numeric(raw["open_price"], errors="coerce").to_numpy(),
            "high": pd.to_numeric(raw["high_price"], errors="coerce").to_numpy(),
            "low": pd.to_numeric(raw["low_price"], errors="coerce").to_numpy(),
            "close": pd.to_numeric(raw["close_price"], errors="coerce").to_numpy(),
            "volume": pd.to_numeric(raw["volume"], errors="coerce").to_numpy(),
            "open_interest": pd.to_numeric(raw["open_interest"], errors="coerce").to_numpy(),
        },
        index=pd.DatetimeIndex(raw["datetime"]),
    )
    df = df.dropna(subset=["close"]).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if df.empty:
        raise ValueError("vn.py 数据清洗后为空")

    df.to_parquet(dataset_path(out_symbol, out_tf))
    ds = register_dataset(db, out_symbol, df, out_tf)
    return {
        "symbol": out_symbol,
        "timeframe": out_tf,
        "rows": ds.rows,
        "start": str(ds.start_date),
        "end": str(ds.end_date),
        "path": str(dataset_path(out_symbol, out_tf)),
    }


def content_hash(df: pd.DataFrame) -> str:
    """数据内容哈希 (用于快照可复现校验)。"""
    hashed = pd.util.hash_pandas_object(df, index=True).values
    return hashlib.sha256(hashed.tobytes()).hexdigest()


def create_snapshot(db: Session, symbol: str, df: pd.DataFrame, timeframe: str = "1d") -> DataSnapshot:
    """为本次回测所用数据建立不可变快照。"""
    snap = DataSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        start_date=df.index.min().date(),
        end_date=df.index.max().date(),
        rows=int(df.shape[0]),
        content_hash=content_hash(df),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap

"""从 vn.py MongoDB (bar_data) 导入 K 线到 QuantLab Parquet。

vn.py 默认库: mongodb://localhost:27017/vnpy
米筐连续合约 (RB888 等) 映射为 QuantLab 品种代码 (RB 等)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.services import market_data

# vn.py 连续合约 -> QuantLab 品种 (与模板/回测一致)
MONGO_SYMBOL_MAP: dict[str, str] = {
    "RB888": "RB",
    "AG888": "AU",
    "CU888": "CU",
    "I888": "I",
    "MA888": "MA",
    "SR888": "SR",
}

DEFAULT_MONGO_URI = "mongodb://localhost:27017/"
DEFAULT_MONGO_DB = "vnpy"
DEFAULT_INTERVAL = "1m"


@dataclass(frozen=True)
class MongoBarSpec:
    symbol: str
    exchange: str
    interval: str = DEFAULT_INTERVAL

    @property
    def quantlab_symbol(self) -> str:
        return MONGO_SYMBOL_MAP.get(self.symbol, self.symbol.replace("888", ""))


def list_mongo_bar_specs(
    mongo_uri: str = DEFAULT_MONGO_URI,
    mongo_db: str = DEFAULT_MONGO_DB,
) -> list[MongoBarSpec]:
    from pymongo import MongoClient

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    col = client[mongo_db]["bar_data"]
    pipeline = [
        {"$group": {"_id": {"symbol": "$symbol", "exchange": "$exchange", "interval": "$interval"}}},
        {"$sort": {"_id.symbol": 1}},
    ]
    specs: list[MongoBarSpec] = []
    for row in col.aggregate(pipeline):
        i = row["_id"]
        sym = str(i.get("symbol") or "")
        if sym.startswith("BTC"):
            continue  # 加密单独处理, 默认不进期货研究库
        specs.append(
            MongoBarSpec(
                symbol=sym,
                exchange=str(i.get("exchange") or ""),
                interval=str(i.get("interval") or DEFAULT_INTERVAL),
            )
        )
    return specs


def _iter_mongo_bars(
    col,
    spec: MongoBarSpec,
    *,
    batch_size: int = 50_000,
) -> Iterator[pd.DataFrame]:
    query = {
        "symbol": spec.symbol,
        "exchange": spec.exchange,
        "interval": spec.interval,
    }
    projection = {
        "_id": 0,
        "datetime": 1,
        "open_price": 1,
        "high_price": 1,
        "low_price": 1,
        "close_price": 1,
        "volume": 1,
        "open_interest": 1,
    }
    cursor = col.find(query, projection).sort("datetime", 1).batch_size(10_000)
    batch: list[dict] = []
    for doc in cursor:
        batch.append(doc)
        if len(batch) >= batch_size:
            yield _docs_to_ohlcv(batch)
            batch = []
    if batch:
        yield _docs_to_ohlcv(batch)


def _docs_to_ohlcv(docs: list[dict]) -> pd.DataFrame:
    raw = pd.DataFrame(docs)
    raw["datetime"] = pd.to_datetime(raw["datetime"], errors="coerce")
    raw = raw.dropna(subset=["datetime"])
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
    return df.dropna(subset=["close"]).sort_index()


def _load_mongo_ohlcv(col, spec: MongoBarSpec) -> pd.DataFrame:
    parts = list(_iter_mongo_bars(col, spec))
    if not parts:
        raise ValueError(f"MongoDB 无数据: {spec.symbol}@{spec.exchange}")
    df = pd.concat(parts)
    return df[~df.index.duplicated(keep="last")]


def resample_ohlcv(df: pd.DataFrame, rule: str = "1D") -> pd.DataFrame:
    agg: dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    if "open_interest" in df.columns:
        agg["open_interest"] = "last"
    daily = df.resample(rule).agg(agg)
    return daily.dropna(subset=["close"])


def import_mongo_spec(
    db: Session,
    col,
    spec: MongoBarSpec,
    *,
    out_symbol: str | None = None,
    write_1m: bool = True,
    write_1d: bool = True,
) -> dict:
    ql_sym = out_symbol or spec.quantlab_symbol
    df_1m = _load_mongo_ohlcv(col, spec)
    result: dict = {
        "mongo_symbol": spec.symbol,
        "exchange": spec.exchange,
        "quantlab_symbol": ql_sym,
        "bars_1m": int(df_1m.shape[0]),
    }

    if write_1m and spec.interval == "1m":
        path_1m = market_data.dataset_path(ql_sym, "1m")
        df_1m.to_parquet(path_1m)
        ds_1m = market_data.register_dataset(db, ql_sym, df_1m, "1m")
        result["1m"] = {"rows": ds_1m.rows, "start": str(ds_1m.start_date), "end": str(ds_1m.end_date)}

    if write_1d:
        df_1d = resample_ohlcv(df_1m, "1D") if spec.interval == "1m" else df_1m
        path_1d = market_data.dataset_path(ql_sym, "1d")
        df_1d.to_parquet(path_1d)
        ds_1d = market_data.register_dataset(db, ql_sym, df_1d, "1d")
        result["1d"] = {"rows": ds_1d.rows, "start": str(ds_1d.start_date), "end": str(ds_1d.end_date)}

    return result


def import_vnpy_mongo(
    db: Session,
    *,
    mongo_uri: str = DEFAULT_MONGO_URI,
    mongo_db: str = DEFAULT_MONGO_DB,
    symbols: list[str] | None = None,
    write_1m: bool = True,
    write_1d: bool = True,
) -> dict:
    from pymongo import MongoClient

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    col = client[mongo_db]["bar_data"]
    specs = list_mongo_bar_specs(mongo_uri, mongo_db)
    if symbols:
        wanted = {s.upper() for s in symbols}
        specs = [s for s in specs if s.symbol.upper() in wanted or s.quantlab_symbol.upper() in wanted]

    imported = []
    for spec in specs:
        imported.append(
            import_mongo_spec(db, col, spec, write_1m=write_1m, write_1d=write_1d)
        )
    return {"imported": imported, "dir": str(market_data.market_dir())}


def register_all_parquet(db: Session) -> dict:
    """扫描 data/market_data/*.parquet 并登记 PG 索引 (Oracle 同步后用)。"""
    out = []
    for path in sorted(market_data.market_dir().glob("*_*.parquet")):
        name = path.stem
        if "_" not in name:
            continue
        symbol, timeframe = name.rsplit("_", 1)
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index)
        ds = market_data.register_dataset(db, symbol, df, timeframe)
        out.append({"symbol": symbol, "timeframe": timeframe, "rows": ds.rows})
    return {"datasets": out}

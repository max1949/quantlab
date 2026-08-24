#!/usr/bin/env python3
"""从 vn.py SQLite 导入 K 线到 QuantLab Parquet。

用法 (仓库根目录):
  python scripts/import-vnpy-bars.py
  python scripts/import-vnpy-bars.py --db C:/Users/Administrator/.vntrader/database.db --symbol RB2605 --interval 1m
  python scripts/import-vnpy-bars.py --resample 1d --symbol RB2605 --out-symbol RB
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.database import SessionLocal
from backend.app.services import market_data


def main() -> None:
    p = argparse.ArgumentParser(description="Import vn.py bar data into QuantLab Parquet")
    p.add_argument("--db", default=str(Path.home() / ".vntrader" / "database.db"))
    p.add_argument("--symbol", default=None, help="Filter / output symbol (vn.py contract code)")
    p.add_argument("--exchange", default=None)
    p.add_argument("--interval", default="1m")
    p.add_argument("--out-symbol", default=None, help="Parquet symbol name (default: same as --symbol or db symbol)")
    p.add_argument("--timeframe", default=None, help="Parquet timeframe label (default: interval)")
    p.add_argument("--resample", default=None, help="Resample to 1d/1h etc before save")
    args = p.parse_args()

    db = SessionLocal()
    try:
        info = market_data.import_vnpy_sqlite(
            db,
            args.db,
            symbol=args.symbol,
            interval=args.interval,
            exchange=args.exchange,
            timeframe=args.timeframe or args.interval,
        )
        out_symbol = args.out_symbol or info["symbol"]
        if args.out_symbol and args.out_symbol != info["symbol"]:
            src = market_data.load_ohlcv(info["symbol"], info["timeframe"])
            src.to_parquet(market_data.dataset_path(out_symbol, info["timeframe"]))
            market_data.register_dataset(db, out_symbol, src, info["timeframe"])
            info["symbol"] = out_symbol

        if args.resample:
            df = market_data.load_ohlcv(info["symbol"], info["timeframe"])
            rule = args.resample.replace("1d", "1D")
            daily = df.resample(rule).agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                    **({"open_interest": "last"} if "open_interest" in df.columns else {}),
                }
            ).dropna(subset=["close"])
            tf = args.resample
            daily.to_parquet(market_data.dataset_path(info["symbol"], tf))
            ds = market_data.register_dataset(db, info["symbol"], daily, tf)
            info.update({"timeframe": tf, "rows": ds.rows, "resampled": True})

        print("imported", info)
    finally:
        db.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""从 vn.py MongoDB 导入 K 线到 QuantLab (Parquet + PG 索引)。

用法 (仓库根目录, 需本机 MongoDB 运行中):
  python scripts/import-vnpy-mongo.py
  python scripts/import-vnpy-mongo.py --symbols RB888,AG888,CU888
  python scripts/import-vnpy-mongo.py --list
  python scripts/import-vnpy-mongo.py --1d-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.database import SessionLocal
from backend.app.services.vnpy_mongo_import import (
    DEFAULT_MONGO_URI,
    list_mongo_bar_specs,
    import_vnpy_mongo,
    register_all_parquet,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Import vn.py MongoDB bars into QuantLab")
    p.add_argument("--mongo-uri", default=DEFAULT_MONGO_URI)
    p.add_argument("--symbols", default="", help="Comma-separated, e.g. RB888,AG888")
    p.add_argument("--list", action="store_true", help="List MongoDB bar specs only")
    p.add_argument("--1d-only", action="store_true", help="Skip 1m parquet (faster, smaller)")
    p.add_argument("--register-only", action="store_true", help="Only scan existing parquet")
    args = p.parse_args()

    if args.list:
        for spec in list_mongo_bar_specs(args.mongo_uri):
            print(f"{spec.symbol}@{spec.exchange} {spec.interval} -> {spec.quantlab_symbol}")
        return

    db = SessionLocal()
    try:
        if args.register_only:
            print(register_all_parquet(db))
            return
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()] or None
        result = import_vnpy_mongo(
            db,
            mongo_uri=args.mongo_uri,
            symbols=symbols,
            write_1m=not args.__dict__["1d_only"],
            write_1d=True,
        )
        for row in result["imported"]:
            print(row)
        print("done", len(result["imported"]), "symbols ->", result["dir"])
    finally:
        db.close()


if __name__ == "__main__":
    main()

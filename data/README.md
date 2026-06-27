# data — 行情与快照存储

V1 存储方案(经评审确认):**PostgreSQL 存索引 + Parquet 存 K 线**,不上 TimescaleDB,以最快开发速度跑通。

```
data/
  market_data/        # 按品种归档的 Parquet K 线
    RB/2025.parquet
    AU/2025.parquet
  raw/                # 原始导入数据 (git 忽略)
  snapshots/          # 回测数据快照, 保证结果可复现 (git 忽略)
```

PostgreSQL 仅保存索引(品种 / 时间范围 / 文件路径),由 Alembic 迁移创建对应索引表。
`raw/`、`snapshots/`、`*.parquet` 已在 `.gitignore` 中忽略。

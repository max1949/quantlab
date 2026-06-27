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

## Sprint 4 落地

- 索引表 `market_datasets`、快照表 `data_snapshots`(迁移 `0005`)。
- 文件命名:`market_data/<symbol>_<timeframe>.parquet`(如 `RB_1d.parquet`)。
- 无真实行情源时,`scripts/seed-market-data.ps1` 用**确定性**样本数据生成 RB/AU/IF;
  真实数据接入后,只需替换 `backend/app/services/market_data.py` 的生成/导入逻辑。
- **可复现**:每次回测建一份 `DataSnapshot`(区间 + 内容哈希),研究报告内嵌该快照信息。

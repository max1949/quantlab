# QuantLab AI - 生成样本行情数据 (Parquet + 索引, 幂等)
# 用法: 在仓库根目录执行  .\scripts\seed-market-data.ps1
# 前置: 已 alembic upgrade head (market_datasets 表存在), PostgreSQL 服务在跑。
# 说明: 没有真实行情源时用确定性样本数据 (RB/AU/IF); 真数据接入后替换生成逻辑即可。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
& $py -c "from backend.app.core.database import SessionLocal; from backend.app.services.market_data import seed_sample_market_data; db=SessionLocal(); print('seed result:', seed_sample_market_data(db)); db.close()"

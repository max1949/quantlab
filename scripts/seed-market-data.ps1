# QuantLab AI - 接入并登记真实行情数据 (Parquet + 索引, 幂等)
# 用法: 在仓库根目录执行  .\scripts\seed-market-data.ps1
# 前置: 已 alembic upgrade head (market_datasets 表存在), PostgreSQL 服务在跑。
# 说明: 优先从 akshare 拉取真实连续主力合约日线 (RB/AU/IF);
#       若离线/数据源异常, 自动退回确定性样本数据, 保证系统永远有可用行情。
#       若本地已有 1m Parquet, 会同步派生 5m/15m/30m/1h 中频周期。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
& $py -c "from backend.app.core.database import SessionLocal; from backend.app.services.market_data import seed_real_market_data, materialize_derived_timeframes; db=SessionLocal(); print('seed result:', seed_real_market_data(db)); print('derived result:', materialize_derived_timeframes(db)); db.close()"

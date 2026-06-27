# QuantLab AI - 创建默认赛季 (幂等)
# 用法: 在仓库根目录执行  .\scripts\seed-season.ps1
# 前置: 已 alembic upgrade head (seasons 表存在), PostgreSQL 服务在跑。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
& $py -c "from backend.app.core.database import SessionLocal; from backend.app.services.competition_service import seed_default_season; db=SessionLocal(); print('season:', seed_default_season(db)); db.close()"

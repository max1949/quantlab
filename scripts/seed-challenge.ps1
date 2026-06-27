# QuantLab AI - 创建默认 30 天研究挑战 (幂等)
# 用法: 在仓库根目录执行  .\scripts\seed-challenge.ps1
# 前置: 已 alembic upgrade head (challenges 表存在)。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
& $py -c "from backend.app.core.database import SessionLocal; from backend.app.services.challenge_service import seed_default_challenge; db=SessionLocal(); print('challenge:', seed_default_challenge(db)); db.close()"

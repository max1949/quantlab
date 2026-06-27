# QuantLab AI - 写入默认学院任务 (幂等, 可重复执行)
# 用法: 在仓库根目录执行  .\scripts\seed-academy.ps1
# 前置: 已 alembic upgrade head (tasks 表存在), PostgreSQL 服务在跑。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
& $py -c "from backend.app.core.database import SessionLocal; from backend.app.services.task_service import seed_default_tasks; db=SessionLocal();
import json;
print('seed result:', seed_default_tasks(db)); db.close()"

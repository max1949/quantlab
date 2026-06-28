# QuantLab AI - 创建默认研究模板 (Sprint 9A, 幂等)
# 用法: 在仓库根目录执行  .\scripts\seed-templates.ps1
# 前置: 已 alembic upgrade head (research_templates 表存在)。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$env:PYTHONPATH = $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
& $py -c "from backend.app.core.database import SessionLocal; from backend.app.services.template_service import seed_default_templates; db=SessionLocal(); print('templates:', seed_default_templates(db)); db.close()"

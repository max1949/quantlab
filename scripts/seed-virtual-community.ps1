# 播种虚拟社区人气数据 (广场 / 榜单 / 关注)
# 用法: 在仓库根目录  .\scripts\seed-virtual-community.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = $Root
if (Test-Path ".venv\Scripts\Activate.ps1") { . .\.venv\Scripts\Activate.ps1 }
if (Test-Path ".env") {
  Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $k, $v = $_.Split('=', 2)
    Set-Item -Path "env:$($k.Trim())" -Value $v.Trim()
  }
}
python -c @"
from backend.app.core.database import SessionLocal
from backend.app.services.example_studies_service import seed_public_example_studies
from backend.app.services.virtual_community_service import seed_virtual_community

db = SessionLocal()
try:
    print('examples:', seed_public_example_studies(db))
    print('community:', seed_virtual_community(db))
finally:
    db.close()
"@

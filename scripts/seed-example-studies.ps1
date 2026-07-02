# 播种公开示例研究 (Feed / SEO)
# 用法: 在仓库根目录执行  .\scripts\seed-example-studies.ps1
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo
$env:PYTHONPATH = $Repo
$py = if (Test-Path "$Repo\.venv\Scripts\python.exe") { "$Repo\.venv\Scripts\python.exe" } else { "python" }
& $py -c @"
from backend.app.core.database import SessionLocal
from backend.app.services.example_studies_service import seed_public_example_studies
db = SessionLocal()
try:
    print(seed_public_example_studies(db))
finally:
    db.close()
"@

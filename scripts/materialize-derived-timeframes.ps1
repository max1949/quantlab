# QuantLab — 从已有 1m Parquet 派生 5m/15m/30m/1h 中频周期 (幂等)
# 用法: 在仓库根目录执行  .\scripts\materialize-derived-timeframes.ps1
# 可选:  .\scripts\materialize-derived-timeframes.ps1 -Symbols RB,AU
# 生产 cron 示例 (每日 18:30):
#   30 18 * * * cd /opt/quantlab && .venv/bin/python -c "from backend.app.core.database import SessionLocal; from backend.app.services.market_data import materialize_derived_timeframes; db=SessionLocal(); print(materialize_derived_timeframes(db)); db.close()"

param(
    [string]$Symbols = ""
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
if ($Symbols) {
    $list = ($Symbols -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join "','"
    $code = "from backend.app.core.database import SessionLocal; from backend.app.services.market_data import materialize_derived_timeframes; db=SessionLocal(); print(materialize_derived_timeframes(db, symbols=['$list'])); db.close()"
} else {
    $code = "from backend.app.core.database import SessionLocal; from backend.app.services.market_data import materialize_derived_timeframes; db=SessionLocal(); print(materialize_derived_timeframes(db)); db.close()"
}
& $py -c $code

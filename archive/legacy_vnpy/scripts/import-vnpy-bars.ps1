# 从本机 vn.py 数据库导入 K 线到 QuantLab (Parquet + PG 索引)
# 用法:
#   .\scripts\import-vnpy-bars.ps1
#   .\scripts\import-vnpy-bars.ps1 -Symbol RB2605 -Interval 1m
#   .\scripts\import-vnpy-bars.ps1 -Symbol RB2605 -Resample 1d -OutSymbol RB2605

param(
  [string]$Db = "$env:USERPROFILE\.vntrader\database.db",
  [string]$Symbol = "",
  [string]$Exchange = "",
  [string]$Interval = "1m",
  [string]$OutSymbol = "",
  [string]$Resample = ""
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo ".venv\Scripts\python.exe"

$args = @("$repo\scripts\import-vnpy-bars.py", "--db", $Db, "--interval", $Interval)
if ($Symbol) { $args += @("--symbol", $Symbol) }
if ($Exchange) { $args += @("--exchange", $Exchange) }
if ($OutSymbol) { $args += @("--out-symbol", $OutSymbol) }
if ($Resample) { $args += @("--resample", $Resample) }

& $py @args

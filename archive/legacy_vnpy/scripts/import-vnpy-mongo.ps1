# 从 vn.py MongoDB 导入 K 线 (最优: 1m + 重采样 1d, 含持仓量)
# 前置: 本机 MongoDB 已运行, vn.py 数据在 vnpy.bar_data
#
# 用法:
#   .\scripts\import-vnpy-mongo.ps1
#   .\scripts\import-vnpy-mongo.ps1 -List
#   .\scripts\import-vnpy-mongo.ps1 -Symbols "RB888,AG888" -DailyOnly
#   .\scripts\sync-vnpy-to-oracle.ps1   # 导入 + 上传 Oracle

param(
  [string]$Symbols = "",
  [switch]$List,
  [switch]$DailyOnly,
  [switch]$RegisterOnly
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
  Write-Error "未找到虚拟环境 $py — 请先在仓库根目录创建 .venv"
}

$args = @("$repo\scripts\import-vnpy-mongo.py")
if ($List) { $args += "--list" }
if ($DailyOnly) { $args += "--1d-only" }
if ($RegisterOnly) { $args += "--register-only" }
if ($Symbols) { $args += @("--symbols", $Symbols) }

& $py @args

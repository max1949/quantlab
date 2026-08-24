# 一键: 本机 MongoDB vn.py 数据 -> Parquet -> 上传 Oracle 并登记索引
# 用法: .\scripts\sync-vnpy-to-oracle.ps1
#       .\scripts\sync-vnpy-to-oracle.ps1 -DailyOnly   # 只传日线 (更快)

param(
  [string]$OracleHost = "144.22.40.92",
  [string]$SshKey = "$env:USERPROFILE\.ssh\oracle_root",
  [string]$Symbols = "",
  [switch]$DailyOnly,
  [switch]$SkipImport
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

if (-not $SkipImport) {
  Write-Host "==> 1/3 从 MongoDB 导入 Parquet ..."
  $importArgs = @()
  if ($Symbols) { $importArgs += @("-Symbols", $Symbols) }
  if ($DailyOnly) { $importArgs += "-DailyOnly" }
  & "$repo\scripts\import-vnpy-mongo.ps1" @importArgs
} else {
  Write-Host "==> 1/3 跳过导入 (使用现有 Parquet)"
}

Write-Host "==> 2/3 上传 Parquet 到 Oracle ..."
$parquetDir = Join-Path $repo "data\market_data"
Get-ChildItem $parquetDir -Filter "*.parquet" | ForEach-Object {
  Write-Host "scp $($_.Name)"
  & scp -i $SshKey $_.FullName "root@${OracleHost}:/opt/quantlab/data/market_data/"
}

Write-Host "==> 3/3 Oracle 登记行情索引 ..."
& scp -i $SshKey "$repo\scripts\register-parquet-oracle.sh" "root@${OracleHost}:/opt/quantlab/scripts/"
& ssh -i $SshKey "root@$OracleHost" "chmod +x /opt/quantlab/scripts/register-parquet-oracle.sh && bash /opt/quantlab/scripts/register-parquet-oracle.sh"

Write-Host "提示: 代码更新请 git push 后 ssh 执行 update-oracle.sh"

Write-Host "Done. Daily bars now sourced from vn.py Mongo data."

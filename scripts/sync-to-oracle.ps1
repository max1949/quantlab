# Windows 本地 -> Oracle 线上：一键导出 DB + 行情文件并触发服务器导入
# 用法: cd C:\Users\Administrator\quantlab ; .\scripts\sync-to-oracle.ps1
#
param(
  [string]$OracleHost = "144.22.40.92",
  [string]$SshKey = "$env:USERPROFILE\.ssh\oracle_root",
  [switch]$SkipImport,
  [switch]$BuildFrontend
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot

& "$PSScriptRoot\export-business-windows.ps1"

if ($BuildFrontend) {
  & (Join-Path $Repo "scripts\build-frontend.ps1")
}

$files = @(
  @{ Local = "C:\Users\Administrator\quantlab_business_inserts_pg10.sql"; Remote = "/tmp/quantlab_business_inserts_pg10.sql" },
  @{ Local = "$Repo\scripts\repair-data-oracle.sh"; Remote = "/opt/quantlab/scripts/repair-data-oracle.sh" },
  @{ Local = "$Repo\scripts\seed-oracle.sh"; Remote = "/opt/quantlab/scripts/seed-oracle.sh" },
  @{ Local = "$Repo\backend\app\services\challenge_service.py"; Remote = "/opt/quantlab/backend/app/services/challenge_service.py" }
)

foreach ($f in $files) {
  Write-Host "scp $($f.Local) -> ${OracleHost}:$($f.Remote)"
  & scp -i $SshKey $f.Local "root@${OracleHost}:$($f.Remote)"
}

$parquetDir = Join-Path $Repo "data\market_data"
Get-ChildItem $parquetDir -Filter "*.parquet" | ForEach-Object {
  Write-Host "scp $($_.Name) -> market_data/"
  & scp -i $SshKey $_.FullName "root@${OracleHost}:/opt/quantlab/data/market_data/"
}

if ($BuildFrontend) {
  $dist = Join-Path $Repo "frontend-react\dist"
  if (Test-Path $dist) {
    Write-Host "scp frontend dist/ ..."
    & scp -i $SshKey -r "$dist\*" "root@${OracleHost}:/opt/quantlab/frontend-react/dist/"
  }
}

if (-not $SkipImport) {
  Write-Host "==> Oracle repair-data-oracle.sh ..."
  & ssh -i $SshKey "root@$OracleHost" "chmod +x /opt/quantlab/scripts/repair-data-oracle.sh /opt/quantlab/scripts/seed-oracle.sh && sudo bash /opt/quantlab/scripts/repair-data-oracle.sh"
}

Write-Host "同步完成。请刷新 https://q.ziyingke.com/app/"

# Windows -> Oracle 全量导出（除 alembic_version 外所有业务表）
# 在本机 PowerShell 运行:
#   cd C:\Users\Administrator\quantlab
#   .\scripts\export-full-windows.ps1
#
$ErrorActionPreference = "Stop"
$PgBin = "C:\quantlab-infra\pgsql\bin"
$OutDir = "C:\Users\Administrator"
$env:PGPASSWORD = "quantlab"

$main = Join-Path $OutDir "quantlab_full_main.sql"
$ai = Join-Path $OutDir "quantlab_full_ai_insights.sql"
$pg10Main = Join-Path $OutDir "quantlab_full_main_pg10.sql"
$pg10Ai = Join-Path $OutDir "quantlab_full_ai_insights_pg10.sql"

Write-Host "==> 主数据（INSERT 格式，PG10 最稳，避免 COPY 多行/JSON 失败）..."
& "$PgBin\pg_dump.exe" -U quantlab -h localhost -d quantlab `
  --data-only --disable-triggers -n quantlab `
  --exclude-table-data=quantlab.alembic_version `
  --exclude-table-data=quantlab.ai_insights `
  --column-inserts -F p -f $main

Write-Host "==> ai_insights（可选，广场/因子不依赖）..."
& "$PgBin\pg_dump.exe" -U quantlab -h localhost -d quantlab `
  --data-only -n quantlab -t quantlab.ai_insights `
  --column-inserts -F p -f $ai

function Remove-PgRestrictLines([string]$In, [string]$Out) {
  $enc = New-Object System.Text.UTF8Encoding $false
  $text = [IO.File]::ReadAllText($In)
  $text = [regex]::Replace($text, '(?m)^\\restrict.*\r?\n', '')
  $text = [regex]::Replace($text, '(?m)^\\unrestrict.*\r?\n', '')
  [IO.File]::WriteAllText($Out, $text, $enc)
}
Remove-PgRestrictLines $main $pg10Main
Remove-PgRestrictLines $ai $pg10Ai

Write-Host ""
Write-Host "已生成:"
Write-Host "  $pg10Main"
Write-Host "  $pg10Ai"
Write-Host ""
Write-Host "上传到 Oracle:"
Write-Host "  scp -i `$env:USERPROFILE\.ssh\oracle_root $pg10Main root@144.22.40.92:/tmp/"
Write-Host "  scp -i `$env:USERPROFILE\.ssh\oracle_root $pg10Ai root@144.22.40.92:/tmp/"
Write-Host "  scp -i `$env:USERPROFILE\.ssh\oracle_root C:\Users\Administrator\quantlab\data\market_data\*.parquet root@144.22.40.92:/opt/quantlab/data/market_data/"

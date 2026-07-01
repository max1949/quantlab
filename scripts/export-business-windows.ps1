# 导出业务数据（不含 users / alembic_version / ai_insights）供 Oracle 补导
# 用法: cd C:\Users\Administrator\quantlab ; .\scripts\export-business-windows.ps1
#
$ErrorActionPreference = "Stop"
$PgBin = "C:\quantlab-infra\pgsql\bin"
$OutDir = "C:\Users\Administrator"
$env:PGPASSWORD = "quantlab"

$raw = Join-Path $OutDir "quantlab_business_inserts.sql"
$out = Join-Path $OutDir "quantlab_business_inserts_pg10.sql"

Write-Host "==> pg_dump INSERT（排除 users / alembic / ai_insights）..."
& "$PgBin\pg_dump.exe" -U quantlab -h localhost -d quantlab `
  --data-only --disable-triggers -n quantlab `
  --exclude-table-data=quantlab.alembic_version `
  --exclude-table-data=quantlab.users `
  --exclude-table-data=quantlab.ai_insights `
  --column-inserts -F p -f $raw

# 不要用 Get-Content 按行写回 — 会破坏多行 INSERT
$enc = New-Object System.Text.UTF8Encoding $false
$text = [IO.File]::ReadAllText($raw)
$text = [regex]::Replace($text, '(?m)^\\restrict.*\r?\n', '')
$text = [regex]::Replace($text, '(?m)^\\unrestrict.*\r?\n', '')
[IO.File]::WriteAllText($out, $text, $enc)

$factorLines = ([regex]::Matches($text, 'INSERT INTO quantlab\.factors')).Count
Write-Host "output: $out"
Write-Host "factors INSERT count: $factorLines (expect 46)"
if ($factorLines -lt 1) { throw 'export failed: no factors' }

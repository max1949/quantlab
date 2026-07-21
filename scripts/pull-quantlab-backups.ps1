# Pull latest QuantLab backups from production to this PC (off-box copy).
# Usage (本机 PowerShell):
#   powershell -ExecutionPolicy Bypass -File scripts/pull-quantlab-backups.ps1
$ErrorActionPreference = "Stop"
$sshKey = "$env:USERPROFILE\.ssh\oracle_root"
$server = "root@144.22.40.92"
$dest = Join-Path $env:USERPROFILE "quantlab-backups"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $dest $stamp

New-Item -ItemType Directory -Force -Path $out | Out-Null
Write-Host "Pulling to $out"

$dailyOk = $false
$weeklyOk = $false
try {
  scp -i $sshKey -o StrictHostKeyChecking=yes -r "${server}:/opt/quantlab/backups/daily/latest" (Join-Path $out "daily-latest")
  $dailyOk = $true
} catch {
  Write-Warning "daily/latest not available yet: $($_.Exception.Message)"
}
try {
  scp -i $sshKey -o StrictHostKeyChecking=yes -r "${server}:/opt/quantlab/backups/weekly/latest" (Join-Path $out "weekly-latest")
  $weeklyOk = $true
} catch {
  Write-Warning "weekly/latest not available yet (run a weekly backup first): $($_.Exception.Message)"
}

if (-not $dailyOk -and -not $weeklyOk) {
  throw "No backups pulled. Ensure server backups exist under /opt/quantlab/backups/"
}

# Keep only last 8 local pull folders
Get-ChildItem $dest -Directory |
  Sort-Object Name -Descending |
  Select-Object -Skip 8 |
  ForEach-Object { Remove-Item $_.FullName -Recurse -Force }

Write-Host "OK — local copies under $out"
Write-Host "Tip: schedule this weekly in Windows Task Scheduler."

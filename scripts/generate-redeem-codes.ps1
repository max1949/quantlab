# Batch-generate monthly card redeem codes (local DB)
# Usage: .\scripts\generate-redeem-codes.ps1
#        .\scripts\generate-redeem-codes.ps1 -Count 20 -Note "July promo"

param(
  [int]$Count = 10,
  [int]$Tier = 1,
  [int]$Days = 30,
  [string]$Plan = "plus_monthly",
  [string]$Note = ""
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$py = Join-Path $repo ".venv\Scripts\python.exe"
$noteArg = if ($Note) { $Note.Replace('"', '') } else { "batch" }

$script = @"
from backend.app.core.database import SessionLocal
from backend.app.services import membership_service as ms

db = SessionLocal()
codes = []
try:
    for _ in range($Count):
        rc = ms.create_redeem_code(db, tier=$Tier, period_days=$Days, plan_code='$Plan', note='$noteArg')
        codes.append(rc.code)
finally:
    db.close()
print('created', len(codes))
for c in codes:
    print(c)
"@

& $py -c $script

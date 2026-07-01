# Apply shared BKTA card-pool migration (QuantLab + ai.ziyingke.com)
# Run from repo root in PowerShell:
#   .\scripts\apply-supabase-redeem-migration.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python scripts/apply-supabase-redeem-migration.py
exit $LASTEXITCODE

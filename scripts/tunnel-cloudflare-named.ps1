# QuantLab AI - Cloudflare named tunnel (fixed hostname q.ziyingke.com)
#
# First-time setup (once):
#   cd C:\Users\Administrator\quantlab
#   .\scripts\tunnel-cloudflare-named.ps1 -Setup
#
# Daily run (after backend is up on :8000):
#   .\scripts\tunnel-cloudflare-named.ps1
#
param(
    [switch]$Setup,
    [string]$Hostname = "q.ziyingke.com",
    [string]$TunnelName = "quantlab",
    [int]$Port = 8000,
    # Use http2 when QUIC/UDP 7844 is flaky (common on some CN networks/firewalls).
    [ValidateSet("auto", "http2", "quic")]
    [string]$Protocol = "http2"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$tools = Join-Path $repo "tools"
$exe = Join-Path $tools "cloudflared.exe"
$configDir = Join-Path $env:USERPROFILE ".cloudflared"
$configFile = Join-Path $configDir "quantlab.yml"
$credNamed = Join-Path $configDir "$TunnelName.json"

function Get-TunnelIdByName {
    param([string]$Name)
    $lines = & $exe tunnel list 2>&1 | Out-String
    foreach ($line in ($lines -split "`n")) {
        if ($line -match "^\s*([0-9a-f-]{36})\s+$Name\s+") {
            return $Matches[1]
        }
    }
    return $null
}

function Ensure-CredentialFile {
    param([string]$Name)
    if (Test-Path $credNamed) {
        return (Get-Content $credNamed -Raw | ConvertFrom-Json).TunnelID
    }
    $tunnelId = Get-TunnelIdByName -Name $Name
    if (-not $tunnelId) {
        return $null
    }
    $credUuid = Join-Path $configDir "$tunnelId.json"
    if (Test-Path $credUuid) {
        Copy-Item $credUuid $credNamed -Force
        return $tunnelId
    }
    return $null
}

function Write-TunnelConfig {
    param([string]$TunnelId, [string]$CredFile)
    $yml = @"
tunnel: $TunnelId
credentials-file: $CredFile

ingress:
  - hostname: $Hostname
    service: http://127.0.0.1:$Port
  - service: http_status:404
"@
    Set-Content -Path $configFile -Value $yml -Encoding ASCII
}

if (-not (Test-Path $exe)) {
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    Write-Host "Downloading cloudflared..." -ForegroundColor Cyan
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $exe
}

if ($Setup) {
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null

    $certFile = Join-Path $configDir "cert.pem"
    if (-not (Test-Path $certFile)) {
        Write-Host "[1/4] Cloudflare login (pick ziyingke.com zone in browser)" -ForegroundColor Cyan
        & $exe tunnel login
    } else {
        Write-Host "[1/4] Cloudflare login skipped (cert.pem already exists)" -ForegroundColor Yellow
    }

    $tunnelId = Ensure-CredentialFile -Name $TunnelName
    if ($tunnelId) {
        Write-Host "[2/4] Reuse existing tunnel: $TunnelName ($tunnelId)" -ForegroundColor Yellow
    } else {
        Write-Host "[2/4] Create tunnel: $TunnelName" -ForegroundColor Cyan
        & $exe tunnel create $TunnelName
        $tunnelId = Ensure-CredentialFile -Name $TunnelName
        if (-not $tunnelId) {
            throw "Credential file not found after tunnel create"
        }
    }

    Write-Host "[3/4] Route DNS: $Hostname" -ForegroundColor Cyan
    & $exe tunnel route dns $TunnelName $Hostname

    Write-TunnelConfig -TunnelId $tunnelId -CredFile $credNamed
    Write-Host "Wrote config: $configFile" -ForegroundColor Green
    Write-Host "[4/4] Done. Run .\scripts\tunnel-cloudflare-named.ps1 to start." -ForegroundColor Green
    exit 0
}

if (-not (Test-Path $configFile)) {
    $tunnelId = Ensure-CredentialFile -Name $TunnelName
    if ($tunnelId) {
        Write-TunnelConfig -TunnelId $tunnelId -CredFile $credNamed
        Write-Host "Recovered config: $configFile" -ForegroundColor Yellow
    } else {
        Write-Host "Not configured yet. Run:" -ForegroundColor Yellow
        Write-Host "  .\scripts\tunnel-cloudflare-named.ps1 -Setup" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting named tunnel -> https://$Hostname/ (local port $Port, protocol $Protocol)" -ForegroundColor Green
& $exe tunnel --config $configFile --protocol $Protocol run $TunnelName

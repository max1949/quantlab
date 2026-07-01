# QuantLab AI - 生产后端 (公网部署用, 配合 Cloudflare Tunnel)
# 用法: 在仓库根目录执行  .\scripts\serve-public.ps1
# 说明:
#   - 监听 127.0.0.1:8000 (隧道在本机连 localhost, 无需开防火墙/路由器)
#   - eager 模式 (回测/验证同进程同步执行, 不需 celery worker)
#   - 启动前确保 PG/Redis 在跑, 并幂等 seed (模板/行情/挑战)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$env:PYTHONPATH = $repo
$py = Join-Path $repo ".venv\Scripts\python.exe"

foreach ($svc in @("postgresql-16", "Redis")) {
    $s = Get-Service $svc -ErrorAction SilentlyContinue
    if ($s -and $s.Status -ne "Running") { Start-Service $svc }
}

# Free port 8000 if a stale uvicorn is still listening.
$port = 8000
$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    Write-Host "Port $port in use (PID $($listener.OwningProcess)) - stopping old backend..." -ForegroundColor Yellow
    Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "Migrating + idempotent seed (templates/market/challenge)..." -ForegroundColor Cyan
Push-Location (Join-Path $repo "backend")
try { & $py -m alembic upgrade head } finally { Pop-Location }
& "$repo\scripts\seed-templates.ps1"
& "$repo\scripts\seed-market-data.ps1"
& "$repo\scripts\seed-challenge.ps1"

Write-Host "Backend (prod): http://127.0.0.1:8000  -> Cloudflare Tunnel" -ForegroundColor Green
& $py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

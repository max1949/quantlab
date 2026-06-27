# QuantLab AI - 启动后端 (本机原生环境, Windows Server)
# 用法: 在仓库根目录下右键 "用 PowerShell 运行", 或终端执行  .\scripts\run-backend.ps1
# 前置: PostgreSQL 服务 postgresql-16 与 Redis 服务 Redis 已安装 (开机自启)。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

# 确保数据/缓存服务在跑
foreach ($svc in @("postgresql-16", "Redis")) {
    $s = Get-Service $svc -ErrorAction SilentlyContinue
    if ($s -and $s.Status -ne "Running") { Start-Service $svc }
}

$py = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "未找到虚拟环境, 正在创建并安装依赖..." -ForegroundColor Yellow
    python -m venv .venv
    & $py -m pip install --upgrade pip
    & $py -m pip install -r backend\requirements.txt
}

Write-Host "后端启动中: http://127.0.0.1:8000  (文档 /docs, 健康检查 /health)" -ForegroundColor Green
& $py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

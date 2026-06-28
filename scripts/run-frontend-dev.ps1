# QuantLab AI - 前端开发服务器 (Sprint 9B, 热更新)
# 用法: 在仓库根目录执行  .\scripts\run-frontend-dev.ps1
# 访问 http://127.0.0.1:5173/app/  (/api 自动代理到本地后端 :8000)
# 前提: 后端已在 :8000 运行 (.\scripts\run-backend.ps1)。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$fe = Join-Path $repo "frontend-react"
Set-Location $fe

if (-not (Test-Path (Join-Path $fe "node_modules"))) {
    Write-Host "首次运行, 安装依赖 (npm install)..."
    npm install
}

npm run dev

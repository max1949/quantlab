# QuantLab AI - 构建 React 前端 (Sprint 9B)
# 用法: 在仓库根目录执行  .\scripts\build-frontend.ps1
# 产物输出到 frontend-react\dist, 由 FastAPI 在 /app 直接服务。

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$fe = Join-Path $repo "frontend-react"
Set-Location $fe

if (-not (Test-Path (Join-Path $fe "node_modules"))) {
    Write-Host "首次构建, 安装依赖 (npm install)..."
    npm install
}

Write-Host "构建前端 (npm run build)..."
npm run build
Write-Host "完成。打开 http://127.0.0.1:8000/app/ 查看 (需后端运行中)。"

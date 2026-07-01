# QuantLab AI - Cloudflare 快速隧道 (把本机 :8000 暴露为公网 https 地址)
# 用法: 先跑 .\scripts\serve-public.ps1, 再在另一个终端跑本脚本。
# 输出形如 https://xxxx.trycloudflare.com 的临时公网地址 (重启会变)。
# 无需 Cloudflare 账号, 无需改路由器/防火墙。
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$tools = Join-Path $repo "tools"
$exe = Join-Path $tools "cloudflared.exe"

if (-not (Test-Path $exe)) {
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    Write-Host "下载 cloudflared..." -ForegroundColor Cyan
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $exe
}

Write-Host "启动隧道 -> http://localhost:8000 (公网地址见下方 trycloudflare.com 链接)" -ForegroundColor Green
& $exe tunnel --url http://localhost:8000

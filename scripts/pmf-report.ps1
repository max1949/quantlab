# QuantLab AI - PMF 只读分析 (v1.0 冻结期, 仅观测, 不改系统)
# 用法: 在仓库根目录执行  .\scripts\pmf-report.ps1            # 全量
#       .\scripts\pmf-report.ps1 -ExcludeTest                 # 排除测试账号
param([switch]$ExcludeTest)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$env:PYTHONPATH = $repo
$py = Join-Path $repo ".venv\Scripts\python.exe"

$args = @("scripts\pmf_report.py")
if ($ExcludeTest) { $args += "--exclude-test" }
& $py @args

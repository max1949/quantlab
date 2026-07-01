# 调用线上 Admin API 批量生成兑换码 (需 Oracle .env 里配置 ADMIN_API_KEY)
# 用法:
#   $env:ADMIN_API_KEY="你的密钥"
#   .\scripts\batch-codes-remote.ps1 -Count 10
#   .\scripts\batch-codes-remote.ps1 -BaseUrl "https://q.ziyingke.com" -Count 20

param(
  [string]$BaseUrl = "https://q.ziyingke.com",
  [int]$Count = 10,
  [int]$Tier = 1,
  [int]$Days = 30,
  [string]$Plan = "plus_monthly",
  [string]$Note = "remote-batch"
)

$ErrorActionPreference = "Stop"
$key = $env:ADMIN_API_KEY
if (-not $key) {
  Write-Error "请先设置环境变量 ADMIN_API_KEY (与服务器 .env 一致)"
}

$body = @{
  count       = $Count
  tier        = $Tier
  period_days = $Days
  plan_code   = $Plan
  note        = $Note
} | ConvertTo-Json

$uri = "$BaseUrl/api/v1/admin/billing/codes/batch"
Write-Host "POST $uri (count=$Count)"
$res = Invoke-RestMethod -Method Post -Uri $uri -Headers @{ "X-Admin-Key" = $key } -ContentType "application/json" -Body $body
Write-Host "created $($res.created)"
$res.codes | ForEach-Object { Write-Host $_ }

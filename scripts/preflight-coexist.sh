#!/usr/bin/env bash
# QuantLab — 共存部署前检查（只读，不修改系统）
# 用法: bash scripts/preflight-coexist.sh
set -euo pipefail

QUANTLAB_PORT="${QUANTLAB_PORT:-8010}"
INSTALL_DIR="${INSTALL_DIR:-/opt/quantlab}"

echo "============================================"
echo " QuantLab 共存检查（只读）"
echo " 目标端口: 127.0.0.1:${QUANTLAB_PORT}"
echo " 安装目录: ${INSTALL_DIR}"
echo "============================================"
echo ""

warn=0
block=0

check_port() {
  local port=$1
  if command -v ss >/dev/null 2>&1; then
    if ss -tln | grep -q ":${port} "; then
      echo "[占用] 端口 ${port} 已被监听:"
      ss -tlnp | grep ":${port} " || true
      if [[ "$port" == "$QUANTLAB_PORT" ]]; then
        block=1
      else
        warn=1
      fi
    else
      echo "[OK] 端口 ${port} 空闲"
    fi
  fi
}

echo "==> 端口"
check_port "$QUANTLAB_PORT"
if [[ "$QUANTLAB_PORT" != "8000" ]]; then
  check_port 8000
fi
echo ""

echo "==> 目录"
if [[ -d "$INSTALL_DIR" ]]; then
  echo "[提示] ${INSTALL_DIR} 已存在（可升级部署，不会删其他目录）"
else
  echo "[OK] ${INSTALL_DIR} 不存在，将新建"
fi
echo ""

echo "==> PostgreSQL"
if command -v psql >/dev/null 2>&1 && sudo -u postgres psql -tAc "SELECT 1" >/dev/null 2>&1; then
  echo "[OK] PostgreSQL 在运行"
  if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='quantlab'" | grep -q 1; then
    echo "[提示] 数据库 quantlab 已存在（脚本会复用，不删其他库）"
  else
    echo "[OK] 将新建独立数据库 quantlab（不影响其他库）"
  fi
else
  echo "[提示] 未检测到本机 PostgreSQL，部署脚本可自动安装，或你提供外部 DATABASE_URL"
fi
echo ""

echo "==> Redis"
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping 2>/dev/null | grep -q PONG; then
  echo "[OK] Redis 在运行"
  echo "[计划] QuantLab 使用 Redis 库 10/11/12（不用 0/1/2，避免和别的站冲突）"
else
  echo "[提示] 未检测到 Redis，部署脚本可自动安装"
fi
echo ""

echo "==> Nginx / Caddy（现有网站）"
for f in /etc/nginx/sites-enabled/*; do
  [[ -e "$f" ]] || continue
  echo "  - nginx: $(basename "$f")"
done
if command -v caddy >/dev/null 2>&1; then
  echo "  - 检测到 Caddy"
fi
echo "[安全] 我们不会改已有站点配置，只新增 q.ziyingke.com 或走 Cloudflare Tunnel"
echo ""

echo "==> systemd"
if systemctl list-unit-files | grep -q '^quantlab.service'; then
  echo "[提示] quantlab.service 已存在"
else
  echo "[OK] 将新建独立服务 quantlab.service"
fi
echo ""

echo "==> 内存（建议 QuantLab 至少 1.5GB 可用）"
free -h 2>/dev/null || true
echo ""

echo "============================================"
if [[ "$block" -eq 1 ]]; then
  echo " 结果: 请换端口，例如 QUANTLAB_PORT=8011 bash scripts/preflight-coexist.sh"
  exit 2
fi
if [[ "$warn" -eq 1 ]]; then
  echo " 结果: 可以部署，但请注意端口/资源占用"
  exit 0
fi
echo " 结果: 可以安全开始共存部署"
echo " 下一步: sudo bash scripts/deploy-coexist.sh"
echo "============================================"

# QuantLab 与现有网站共存部署

## 安全原则（不会影响别的站）

| 项目 | 做法 |
|------|------|
| 代码 | 独立目录 `/opt/quantlab` |
| 数据库 | 只新建 `quantlab` 库，**不删不改**其他库 |
| Redis | 用 **10/11/12** 号库，不用 0/1/2 |
| 端口 | 默认 **8010**，只绑 `127.0.0.1` |
| 进程 | 独立 `quantlab.service`，带内存/CPU 上限 |
| Nginx | **不改**现有站点，只可选新增 `q.ziyingke.com` |
| 公网 | 推荐 **Cloudflare Tunnel** 单独指到 8010 |

## 第一步：只读检查（本机 SSH 里）

```bash
git clone https://github.com/max1949/quantlab.git /tmp/quantlab-check
cd /tmp/quantlab-check
bash scripts/preflight-coexist.sh
```

若 8010 被占用：

```bash
QUANTLAB_PORT=8011 bash scripts/preflight-coexist.sh
```

## 第二步：共存部署

机器上 **已有 PostgreSQL / Redis** 时：

```bash
cd /tmp/quantlab-check   # 或 /opt/quantlab
sudo SKIP_INSTALL_PG=1 SKIP_INSTALL_REDIS=1 QUANTLAB_PORT=8010 bash scripts/deploy-coexist.sh
```

全新辅助安装 PG/Redis 时：

```bash
sudo QUANTLAB_PORT=8010 bash scripts/deploy-coexist.sh
```

验证：

```bash
curl http://127.0.0.1:8010/health
```

**不要动**现有网站的 Nginx/Caddy 配置，直到本机 health 通过。

## 第三步：对外暴露 q.ziyingke.com

### 方案 A — Cloudflare Tunnel（推荐，零风险）

在 Oracle 机上给 cloudflared **多加一条 ingress**（或单独一个小隧道）：

```yaml
ingress:
  - hostname: q.ziyingke.com
    service: http://127.0.0.1:8010
  # 下面保留你现有网站的规则...
  - service: http_status:404
```

重载 cloudflared 后，**只有 q 子域走 QuantLab**，别的域名不变。

### 方案 B — Nginx 新 server 块

新建 `/etc/nginx/sites-available/q.ziyingke.com`（**不要改**别的文件）：

```nginx
server {
    listen 80;
    server_name q.ziyingke.com;
    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/q.ziyingke.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

`nginx -t` 失败则 **不要 reload**，现有站不受影响。

## 回滚（1 分钟）

```bash
sudo systemctl stop quantlab
sudo systemctl disable quantlab
# 删除 nginx 软链（若用了方案 B）
# sudo rm /etc/nginx/sites-enabled/q.ziyingke.com && sudo nginx -t && sudo systemctl reload nginx
```

可选删库（**只删 quantlab**，别删别的）：

```bash
sudo -u postgres psql -c "DROP DATABASE IF EXISTS quantlab;"
```

## 资源建议

同机已有多个站时，Oracle 免费机建议 QuantLab 用 **2 OCPU 里划 1 个逻辑核** 即可；`deploy-coexist.sh` 已设 `MemoryMax=2G`。

若整机内存紧张（<2G 可用），先 `free -h` 发我，再决定是否部署。

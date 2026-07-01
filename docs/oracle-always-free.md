# Oracle Cloud Always Free — QuantLab 部署指南

## 你能拿到什么（永久免费）

| 资源 | 额度 |
|------|------|
| CPU | 最多 **4 核** ARM (Ampere A1) |
| 内存 | 最多 **24 GB** |
| 硬盘 | **200 GB** 块存储 |
| 流量 | 出站约 **10 TB/月** |
| 公网 IP | 1 个 |

够跑 QuantLab：FastAPI + PostgreSQL + Redis + Cloudflare Tunnel。

---

## 第一步：注册账号

1. 浏览器打开：**https://www.oracle.com/cloud/free/**
2. 点 **Start for free**，用邮箱注册
3. 选 **Home Region**（地区选好后**不能改**，建议）：
   - 国内访问：优先 **Japan East (Tokyo)** 或 **South Korea Central (Seoul)**
   - 抢不到机器可试 **India West (Mumbai)**
4. 验证身份：需要 **信用卡/借记卡**（只验证，Always Free 内不扣费）
5. 注册完成后登录控制台：**https://cloud.oracle.com/**

### 常见卡点

- **注册失败 / 卡验证不过**：换一张卡，或联系银行放行境外小额验证
- **一直 Free Tier 建不了 A1 机器**：控制台右上角 → **Upgrade to Pay As You Go**
  - 只要实例规格选 **Always Free-eligible**，不超免费额度，**不会自动扣费**
  - 升级后更容易抢到 ARM 机器（Oracle 官方也这么建议）

### 建议立刻做：预算告警

1. 控制台搜索 **Budgets**
2. 新建预算，例如每月 **$1**，超了发邮件
3. 这样心里踏实，避免误开付费资源

---

## 第二步：本机生成 SSH 密钥（Windows PowerShell）

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\oracle_quantlab -N '""'
Get-Content $env:USERPROFILE\.ssh\oracle_quantlab.pub
```

复制输出的 **一整行**（以 `ssh-ed25519` 开头），后面创建实例时要粘贴。

---

## 第三步：创建免费虚拟机

1. 控制台左上角 **☰** → **Compute** → **Instances**
2. **Create instance**
3. 填写：
   - **Name**：`quantlab`
   - **Image**：**Ubuntu 22.04**（或 24.04 Minimal **aarch64**）
   - **Shape**：点 **Change shape**
     - 选 **Ampere** → **VM.Standard.A1.Flex**（带 Always Free 标记）
     - 推荐 QuantLab：**2 OCPU + 12 GB RAM**（够用且省额度）
     - 想拉满免费：**4 OCPU + 24 GB RAM**
   - **Networking**：勾选 **Assign a public IPv4 address**
   - **SSH keys**：选 **Paste public key**，粘贴上一步的公钥
   - **Boot volume**：建议 **50 GB**（够装系统+数据库+行情数据）
4. 点 **Create**

### 若报错 `Out of host capacity`

很常见，不是你没做对。按顺序试：

1. **换 Availability Domain**（AD-1 / AD-2 / AD-3 都试）
2. **换区域**（需新账号或另开 region 的 compartment，一般先在同区多试几次）
3. **改小配置**：先 1 OCPU + 6 GB 创建，成功后再改大
4. **错峰**：凌晨或工作日白天多试几次
5. **Upgrade Pay As You Go** 后再试

创建成功后，记下实例页的 **Public IP**（例如 `123.45.67.89`）。

---

## 第四步：放行 SSH（安全组）

1. 实例详情页 → **Subnet** 链接 → **Security List**
2. **Add Ingress Rules**：
   - Source CIDR：`0.0.0.0/0`
   - Protocol：**TCP**
   - Port：**22**
3. 保存

> QuantLab 若继续用 **Cloudflare Tunnel**，不必开放 80/443，只开 22 即可。

---

## 第五步：SSH 登录服务器

PowerShell：

```powershell
ssh -i $env:USERPROFILE\.ssh\oracle_quantlab ubuntu@你的公网IP
```

第一次会问 `Are you sure...`，输入 `yes`。

---

## 第六步：一键部署 QuantLab

在服务器上执行：

```bash
curl -fsSL https://raw.githubusercontent.com/max1949/quantlab/master/scripts/deploy-oracle-ubuntu.sh | sudo bash
```

或先克隆再跑：

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/max1949/quantlab.git /opt/quantlab
sudo bash /opt/quantlab/scripts/deploy-oracle-ubuntu.sh
```

检查：

```bash
curl http://127.0.0.1:8000/health
```

应返回 `{"status":"ok",...}`。

---

## 第七步：接上 Cloudflare（q.ziyingke.com）

### 方案 A：继续用命名隧道（推荐）

1. 在 Oracle 服务器安装 cloudflared（与 Windows 相同逻辑）
2. 把本机 `~/.cloudflared/quantlab.yml` 和凭证复制到服务器
3. 把配置里的 `service` 改为 `http://127.0.0.1:8000`
4. `systemctl enable --now cloudflared`

### 方案 B：DNS 指到 Oracle 公网 IP

1. Cloudflare 把 `q` 记录改为 **A 记录** → Oracle 公网 IP
2. 服务器前加 Nginx + HTTPS（需开放 80/443）

你现有环境用 **方案 A** 改动最小。

---

## 第八步：关掉本机 Windows 托管（迁移完成后）

1. 确认 `https://q.ziyingke.com/health` 正常
2. 本机停掉 `serve-public.ps1` 和 `cloudflared`
3. 以后 Oracle 24 小时在线，**本机可以关机**

---

## 费用与避坑

| 会做 | 不会扣费 |
|------|----------|
| A1 Flex 在 4OCPU/24G 以内 | ✅ |
| 200G 块存储以内 | ✅ |
| 误开 x86 大机型、负载均衡、多余公网 IP | ❌ 可能扣费 |

创建实例时务必确认 Shape 旁有 **Always Free-eligible**。

---

## 你需要发给我的信息（部署隧道时）

1. Oracle 实例 **公网 IP**
2. SSH 能否登录成功
3. `curl http://127.0.0.1:8000/health` 结果

我可以帮你写 **cloudflared systemd** 和 **从 Windows 迁隧道** 的具体命令。

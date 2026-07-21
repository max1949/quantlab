# QuantLab Backup & Restore（生产机）

预防数据被删/被改/机房故障：每天自动备份数据库与密钥配置，必要时一键恢复。

## 三重备份

| 层 | 位置 | 内容 |
|----|------|------|
| ① 服务器本机 | `/opt/quantlab/backups/` | 明文 dump（恢复最快） |
| ② 本机拉回 | `C:\Users\Administrator\quantlab-backups\` | 离线第二份 |
| ③ 云端 | 私有仓库 `quantlab-backups` Releases | **仅加密包**（防整机被黑） |

**不要**把明文数据库或 `.env` 推到普通 GitHub 代码仓库。云端只接受 AES 加密后的文件。

## 已包含内容（本机每次备份）

| 文件 | 说明 |
|------|------|
| `quantlab.dump` | PostgreSQL 完整库（custom 格式） |
| `quantlab.dump.sha256` | 校验和 |
| `.env` | 密钥与数据库连接（权限 600） |
| `meta.txt` | 时间、git 版本、主机名 |

保留策略默认：每日 **14** 天，每周 **8** 周；云端 stamped release 默认保留 **16** 份。

## 开通 GitHub 云端备份（一次）

1. 已创建私有仓库：`https://github.com/max1949/quantlab-backups`（仅放加密备份）
2. 准备 GitHub Token（classic `repo` 或 fine-grained：对该仓库 Contents + Releases 写权限）
3. 在服务器执行：

```bash
sudo GITHUB_BACKUP_TOKEN='你的token' bash /opt/quantlab/scripts/setup-quantlab-github-backup.sh
```

脚本会：

- 生成加密密钥 `/opt/quantlab/.backup_encryption_key`
- 写入 `/opt/quantlab/.backup_offsite.env`（权限 600）
- 立刻做一次日备份并上传到 GitHub Releases

**务必把加密密钥拷回本机保存**（U 盘/密码管理器）。没有密钥，云端备份解不开。

本机保存示例（PowerShell）：

```powershell
$key = "$env:USERPROFILE\.ssh\oracle_root"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\quantlab-backup-secrets" | Out-Null
scp -i $key root@144.22.40.92:/opt/quantlab/.backup_encryption_key "$env:USERPROFILE\quantlab-backup-secrets\"
```

## 日常定时

```bash
# 安装/刷新定时任务（每天 03:40、每周日 05:10；含云端上传）
sudo bash /opt/quantlab/scripts/install-quantlab-backup-cron.sh
```

手动：

```bash
sudo bash /opt/quantlab/scripts/backup-quantlab.sh daily
sudo bash /opt/quantlab/scripts/backup-quantlab.sh weekly
```

云端查看：`https://github.com/max1949/quantlab-backups/releases`  
滚动指针：`quantlab-daily-latest` / `quantlab-weekly-latest`

## 恢复

### A. 从本机备份恢复

```bash
sudo bash /opt/quantlab/scripts/restore-quantlab.sh --list
sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab.sh --latest daily
```

### B. 从 GitHub 云端恢复（本机备份没了时）

```bash
# 最新日备份
sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab-from-github.sh daily

# 指定 stamped tag
sudo QUANTLAB_RESTORE_CONFIRM=YES bash /opt/quantlab/scripts/restore-quantlab-from-github.sh daily backup-daily-20260721T164731Z
```

## 本机再拉一份（可选）

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\quantlab\scripts\pull-quantlab-backups.ps1
```

## 与“防黑客”的关系

1. 本机备份：防误删、防坏库  
2. 加密云端：防整台服务器被清空  
3. 加密密钥离线保存：防“云仓被盗仍可读”  
4. SSH 密钥登录、`.env` 权限 600  

## 注意

- 恢复会覆盖当前数据库；必须设置 `QUANTLAB_RESTORE_CONFIRM=YES`
- 恢复前本地脚本会再打一份 `pre-restore` 安全备份
- Redis 不备份（可重建）
- 关闭云端上传（仅本机）：`QUANTLAB_OFFSITE=0 bash /opt/quantlab/scripts/backup-quantlab.sh daily`

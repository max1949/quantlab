# QuantLab AI — Backend

FastAPI 后端。遵循分层:`api`(薄路由)→ `services`(业务)→ `models`(ORM),
认证原语集中在 `auth`,出入参在 `schemas`。重计算不在此进程(走 Celery Worker)。

## 目录

```
app/
├── main.py            # 装配 + /health
├── api/v1/            # 路由层 (薄, 只编排)
│   └── routes/        # auth.py · users.py · ...
├── core/              # config (env) · database (Session/Base)
├── models/            # ORM: user.py (User, UserLevel) · task.py (Task, UserTask)
├── schemas/           # Pydantic: user.py · task.py
├── services/          # 业务: user_service.py · task_service.py · leveling.py
└── auth/              # security.py (hash/JWT) · deps.py (当前用户/等级闸门)
migrations/            # Alembic (0001 baseline · 0002 users · 0003 academy)
tests/                 # pytest (SQLite 内存库)
```

## Sprint 1 — 用户系统

### 数据模型 `User`

| 字段 | 说明 |
|---|---|
| `id` | UUID 主键 (客户端生成, 跨方言) |
| `email` / `username` | 唯一 + 索引 |
| `hashed_password` | bcrypt 哈希 (绝不出参) |
| `level` | 研究员等级,默认 `L0`。语义见 `UserLevel` |
| `research_score` | 研究积分占位 (Sprint 6 动态评分写入) |
| `is_active` | 软禁用 |
| `created_at` / `updated_at` | 时间戳 |

**等级 `UserLevel`(能力闸门,Level 决定能力):**

| 值 | 名称 | 能力 |
|---|---|---|
| L0 | 观察员 | 只读 + 模板因子 |
| L1 | 研究学徒 | 因子组合器 |
| L2 | 研究员 | 自定义 Python 因子 (沙箱) |
| L3 | 高级研究员 | vn.py 模拟/实盘 |

用 `IntEnum`,权限判断退化为数值比较。受限路由用
`Depends(require_level(UserLevel.Lx))` 声明所需最低等级(Sprint 2 起广泛使用)。

### 接口

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/api/v1/auth/register` | 注册 (默认 L0) → `UserOut` | 否 |
| POST | `/api/v1/auth/login` | 登录 (邮箱或用户名) → `{access_token}` | 否 |
| GET | `/api/v1/users/me` | 当前用户 | Bearer JWT |

JWT:HS256,载荷 `sub`(用户 id)/`type`/`iat`/`exp`,密钥与有效期见 `.env`
(`SECRET_KEY` / `ACCESS_TOKEN_EXPIRE_MINUTES`)。

### 示例

```bash
# 注册
curl -X POST localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@quantlab.ai","username":"alice","password":"s3cret-pass"}'

# 登录拿令牌
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"identifier":"alice","password":"s3cret-pass"}' | jq -r .access_token)

# 受保护接口
curl localhost:8000/api/v1/users/me -H "Authorization: Bearer $TOKEN"
```

## 运行

```bash
# 容器方式 (推荐, 见仓库根 README)
docker compose up -d postgres redis backend
docker compose exec backend alembic -c backend/alembic.ini upgrade head

# 本机方式
pip install -r requirements.txt
cd backend && alembic upgrade head
uvicorn backend.app.main:app --reload   # 在仓库根执行, 保证 backend 包可导入
```

迁移在 `backend/` 下执行(`alembic.ini` 的 `script_location = migrations`)。
新增模型后:`alembic revision --autogenerate -m "..."` → 审阅 → `alembic upgrade head`。

## Sprint 2 — 学院系统(任务 · 等级成长 · 等级绑定权限)

### 成长模型

- `User.experience`:累计经验(单调递增)。
- 等级由经验阈值推导(`services/leveling.py`):

| 等级 | 累计经验阈值 |
|---|---|
| L0 | 0 |
| L1 | 100 |
| L2 | 300 |
| L3 | 700 |

完成任务 → `experience += xp_reward` → 经阈值重算等级(只升不降)。

### 数据模型

- `Task`:`code`(唯一编码)/ `title` / `description` / `category` / **`min_level`**(解锁所需等级)/ `xp_reward` / `order_index` / `is_active`。
- `UserTask`:用户完成记录,`(user_id, task_id)` 唯一(保证幂等)。

**等级绑定权限**:`Task.min_level` 决定可见/可完成。用户等级不足时任务 `locked`,
完成请求返回 403。这与 `auth/deps.py::require_level` 是同一套"Level 决定能力"的落地。

### 接口(均需 Bearer JWT)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/tasks` | 任务列表(含 `locked` / `completed` 状态) |
| GET | `/api/v1/tasks/{code}` | 任务详情 |
| POST | `/api/v1/tasks/{code}/complete` | 完成任务(结算经验/升级;`min_level` 闸门:403;重复:409) |

`UserOut` 增补 `experience` 与 `experience_to_next_level`。

### 种子任务

预置一条 L0→L3 的成长主线(`task_service.DEFAULT_TASKS`)。幂等写入:

```powershell
.\scripts\seed-academy.ps1     # 或在仓库根: python -c "...seed_default_tasks(SessionLocal())"
```

## 测试

```bash
cd backend && pytest          # 用 SQLite 内存库, 不需 Postgres  (26 passed)
```

覆盖:**Sprint 1** — 注册(成功/重复/弱口令/非法邮箱)、登录(邮箱与用户名/错密码/未知用户)、
`/users/me`(有效/缺失/非法令牌)、密码哈希与 JWT 往返、等级闸门;
**Sprint 2** — 经验阈值升级、任务列表锁定/进度、完成奖励、升级、`min_level` 403、重复完成 409、需鉴权。

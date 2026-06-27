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
├── models/            # ORM: user · task · factor · market · backtest
├── schemas/           # Pydantic: user · task · factor · backtest
├── services/          # user · task · leveling · factor · market_data · backtest
├── tasks/             # Celery: celery_app · backtest_tasks
└── auth/              # security.py (hash/JWT) · deps.py (当前用户/等级闸门)
migrations/            # Alembic (0001..0005: baseline/users/academy/factors/backtests)
tests/                 # pytest (SQLite 内存库; 含 ../engine/tests)
```

> 计算与 Web 解耦: 计算逻辑在 `engine/`(纯函数), service 仅做持久化/权限/编排。
> 重计算(回测)走 Celery worker, 与 API 解耦。

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

## Sprint 3 — 因子实验室(模板因子 · 组合器)

计算在 `engine/factor_engine.py`(纯函数);后端只管定义、持久化、权限。

### 数据模型 `Factor`

`owner_id` / `name`(同人唯一)/ `kind`(`template` | `stack`)/ `template_type` /
`spec`(JSON 定义)/ `version`。

- `template`:`spec = {"params": {...}}`
- `stack`:`spec = {"components": [{"factor_id", "weight"}, ...]}`

**等级绑定权限**:模板因子 L0 可建;**组合器需 L1**(路由用 `require_level(UserLevel.L1)`,
对应"L0 模板 → L1 组合器")。

### 接口(均需 Bearer JWT)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/factors/templates` | 模板因子目录(含参数规格) |
| GET | `/api/v1/factors` | 我的因子列表 |
| POST | `/api/v1/factors/template` | 创建模板因子(L0+) |
| POST | `/api/v1/factors/stack` | 创建组合器(**需 L1**;不足 403) |
| GET | `/api/v1/factors/{id}` | 因子详情 |
| POST | `/api/v1/factors/{id}/preview` | 在样本行情上预览(返回摘要统计) |
| DELETE | `/api/v1/factors/{id}` | 删除因子 |

预览使用 `engine.sample_price_frame`(确定性);真实行情数据在 Sprint 4 接入。

## Sprint 4 — 回测系统(成本 · 研究报告 · 数据快照 · 异步)

计算在 `engine/`(cost_model / backtest / report);后端负责数据、快照、编排与异步。

### 数据存储 V1

PostgreSQL 存索引 + Parquet 存 K 线。`MarketDataset`(品种/周期/区间/行数/路径),
`DataSnapshot`(区间 + 内容哈希,**保证回测可复现**)。无真实行情源时用确定性样本数据:

```powershell
.\scripts\seed-market-data.ps1     # 生成 RB/AU/IF 样本 Parquet + 登记索引
```

### 异步回测(Celery)

`POST /backtests` 只创建回测(`pending`)并**入队**,真正计算在 **Celery worker** 执行:
绑定因子 + 数据快照 + 成本配置 → 跑 `engine.run_backtest` → 落库指标/净值/研究报告 →
状态 `success`/`failed`。`GET /backtests/{id}` 轮询结果。

启动 worker(本机原生,Windows 用 solo 池):

```powershell
.\.venv\Scripts\python.exe -m celery -A backend.app.tasks.celery_app worker --loglevel=info --pool=solo
```

> 测试用 `celery_task_always_eager=True` 同步执行,不需 worker/Redis。

### 接口(均需 Bearer JWT)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/datasets` | 可用行情数据集 |
| POST | `/api/v1/backtests` | 创建并运行回测(异步;返回 `pending`/结果) |
| GET | `/api/v1/backtests` | 我的回测列表 |
| GET | `/api/v1/backtests/{id}` | 回测详情(状态/指标/净值/研究报告) |

## 测试

```bash
cd backend && pytest          # 用 SQLite 内存库, 不需 Postgres  (67 passed, 含 engine)
```

覆盖:**Sprint 1** — 注册/登录/`me`/密码哈希/JWT/等级闸门;
**Sprint 2** — 经验升级、任务锁定/完成、`min_level` 403、重复 409;
**Sprint 3** — 模板目录、建因子、参数校验、组合器 L0→403/L1→201、预览;
**Sprint 4** — 数据集列表、回测成功、指标/研究报告/净值、快照绑定、成本影响、错误分支、鉴权;
**engine** — 因子(模板/标准化/组合器)、成本、回测指标、研究报告评级。

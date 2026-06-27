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
├── models/            # ORM: user.py (User, UserLevel)
├── schemas/           # Pydantic: user.py
├── services/          # 业务: user_service.py
└── auth/              # security.py (hash/JWT) · deps.py (当前用户/等级闸门)
migrations/            # Alembic (0001 baseline · 0002 users)
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

## 测试

```bash
cd backend && pytest          # 用 SQLite 内存库, 不需 Postgres
```

覆盖:注册(成功/重复/弱口令/非法邮箱)、登录(邮箱与用户名/错密码/未知用户)、
`/users/me`(有效/缺失/非法令牌)、密码哈希与 JWT 往返、等级闸门。

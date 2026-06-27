# QuantLab AI

> AI 量化研究员孵化与因子研究平台 —— 量化领域的 **GitHub + Kaggle + 研究员培养系统**。
>
> 本仓库不是"做一个回测网站"。核心资产是 **研究行为数据 + 可复现的研究过程**,目标是沉淀 AI 量化研究基础设施。

当前阶段:**Sprint 1 — 项目骨架(已搭建,暂不含业务逻辑)**。

---

## 顶层结构(最终形态)

```
                QuantLab AI
                    |
   ----------------------------------
   Academy                 Research Arena
   (小白成长)               (因子竞争)
      |                         |
      ----- Research Graph ------
                  |
          AI Quant Dataset
                  |
           人才 / 企业服务
```

- **Academy(量化学院)**:任务驱动,把零基础用户从观察员培养为研究员。
- **Research Arena(竞技系统)**:Research Season 赛季 + 排行榜 + 研究积分,提供"每天回来"的行为闭环。
- **Research Graph**:研究行为以节点/边沉淀为知识图谱(假设 → 测试 → 失败 → 优化 → 成功),构成长期 AI 训练价值。

---

## 设计哲学(决定项目能否"进化")

| 原则 | 架构影响 |
|---|---|
| 一切研究皆可复现 | 因子版本化 + 回测绑定数据快照,任何结果可精确重跑 |
| 研究过程 > 研究结果 | `ResearchEvent` 事件流 + Research Graph,记录失败与迭代 |
| 计算与 Web 解耦 | API 不做重计算,回测/验证走 Celery Worker |
| 不可信代码默认有罪 | 用户 Python 因子在物理隔离沙箱执行(后置开放) |

---

## 已纳入的 7 项架构修正(评审通过)

1. **Research Competition 层**:新增 `Season` / `SeasonTask`,以赛季驱动留存。
2. **Research Graph**:`ResearchEvent` 升级为 `ResearchNode` / `ResearchEdge` 知识图谱。
3. **动态评分(Dynamic Research Score)**:`final = base × decay`,防止失效老因子霸榜。
4. **等级绑定权限**:Level 决定能力(L0 模板 → L1 组合器 → L2 Python → L3 vn.py)。
5. **回测产出研究报告**:不仅给数字,生成可读的"研究报告"(假设/方法/结果/结论)。
6. **数据存储 V1**:PostgreSQL 存索引 + Parquet 存 K 线(不上 TimescaleDB)。
7. **vn.py 前移**:Sprint 6 预留小接口,模拟交易作为强刺激尽早出现(Sprint 8 完整接入)。

---

## 技术栈

- 前端:Next.js · React · TailwindCSS
- 后端:Python · FastAPI
- 异步计算:Celery + Redis
- 数据库:PostgreSQL(业务/研究元数据);行情:Parquet + PG 索引
- 计算引擎:Pandas · NumPy · scikit-learn(`engine/` 纯函数库)
- 部署:Docker Compose;后期接入 vn.py

---

## 目录结构

```
quantlab/
├── docker-compose.yml      # 一键编排 (postgres / redis / backend / worker)
├── .env.example            # 环境变量样例
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 入口 (仅装配 + 健康检查)
│   │   ├── api/v1/         # 路由层 (薄, 只编排)
│   │   ├── core/           # 配置 / 数据库会话
│   │   ├── models/         # ORM 模型 (按 Sprint 定义)
│   │   ├── schemas/        # Pydantic 出入参
│   │   ├── services/       # 业务逻辑
│   │   ├── auth/           # JWT / 等级权限
│   │   └── tasks/          # Celery
│   ├── migrations/         # Alembic 迁移
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── engine/                 # 纯函数计算库 (无 Web 依赖, 可独立测试)
│   ├── factor_engine.py · cost_model.py · backtest.py
│   ├── walk_forward.py · scoring.py
│   └── tests/
├── sandbox/                # 用户 Python 因子隔离执行 (后置开放)
├── frontend/               # Next.js (后续 Sprint 初始化)
├── data/                   # market_data (Parquet) / raw / snapshots
└── infra/
    ├── db/init.sql         # PostgreSQL 初始化 (扩展 / schema)
    └── scripts/
```

---

## Sprint 路线(修订后,锁定开发节奏)

| Sprint | 主题 | 交付 |
|---|---|---|
| 1 | 基础骨架 | Docker · 数据库 · 用户 |
| 2 | 学院系统 | 任务 · 等级 · 成长(等级绑定权限) |
| 3 | 因子实验室 | 模板因子 · 组合器 |
| 4 | 回测系统 | 成本 · **研究报告** · 数据快照 |
| 5 | 验证系统 | OOS · Walk-Forward · Decay |
| 6 | 竞技系统 | Season · 排行榜 · 研究积分(+ vn.py 接口预留) |
| 7 | AI 助手 | 研究建议 · 报告总结(外部 LLM API) |
| 8 | 模拟交易 | vn.py 接口完整接入 |

> 开发纪律:按 Sprint 锁死推进。每个模块必须 **可运行 + 有测试 + 有 README**。

---

## 本地运行

### A. 本机原生环境(当前 Windows Server,已搭好)

本机是 Windows Server 2019,**不支持 Docker Desktop**(详见"当前进度"),因此用原生服务:

- PostgreSQL 16.14:Windows 服务 `postgresql-16`(开机自启),端口 `5432`
  - 二进制 `C:\quantlab-infra\pgsql`,数据目录 `C:\quantlab-infra\pgdata`
  - 业务库/角色 `quantlab` / `quantlab`,schema `quantlab`(扩展 pgcrypto、pg_trgm 已建)
- Redis 5:Windows 服务 `Redis`(开机自启),端口 `6379`
- Python venv:`.venv`(已装 `backend/requirements.txt`)

```powershell
# 启动后端 (会自动确保两个服务在跑)
.\scripts\run-backend.ps1
# 等价于:
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 健康检查 / 文档
#   http://127.0.0.1:8000/health   ->  {"status":"ok"}
#   http://127.0.0.1:8000/docs     ->  Swagger UI

# 数据库迁移 (在 backend/ 下)
cd backend; ..\.venv\Scripts\python.exe -m alembic upgrade head

# 生成样本行情数据 (回测用)
.\scripts\seed-market-data.ps1

# 启动 Celery worker (回测异步计算; Windows 用 solo 池)
.\.venv\Scripts\python.exe -m celery -A backend.app.tasks.celery_app worker --loglevel=info --pool=solo

# 测试
cd backend; ..\.venv\Scripts\python.exe -m pytest
```

服务管理:`Get-Service postgresql-16,Redis` / `Restart-Service postgresql-16`。

### B. Docker Compose(将来的 Linux 部署机)

```bash
cp .env.example .env
# 注意: 容器内 DATABASE_URL / REDIS_URL 的 host 用服务名 postgres / redis
docker compose up -d postgres redis backend
curl http://localhost:8000/health
docker compose exec backend alembic -c backend/alembic.ini upgrade head
docker compose --profile workers up -d worker   # 可选: Celery worker
```

---

## 当前进度

- [x] Sprint 1 骨架:Docker Compose / 目录结构 / PostgreSQL 初始化 / Alembic / README
- [x] Sprint 1 业务:用户系统(User 模型 + 注册/登录 + JWT + 等级字段)
  - `User` 模型:email / username / hashed_password / **level (L0–L3)** / research_score / is_active / 时间戳
  - 接口:`POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/users/me`
  - JWT(HS256)+ bcrypt 密码哈希;等级闸门 `require_level()`(Sprint 2 启用)
  - Alembic 迁移 `0002_users`;后端测试 `backend/tests/`(SQLite 内存库)
  - 细节见 `backend/README.md`
- [x] Sprint 1 验证(2026-06-27):
  - `pytest` 16 用例全绿;`/health`、`/api/v1/ping` 正常;路由表正确
  - `alembic upgrade head` 链路 `0001 → 0002` 成功,`users` 表字段/索引符合设计
- [x] 本机环境搭建(2026-06-28):原生 PostgreSQL 16 + Redis 5(均为开机自启服务)
  - 后端连**真库**端到端跑通:注册 → 登录 → JWT → `/users/me`,错误密码 401,数据已落库
- [x] git 初始化 + 首次提交(Sprint 1 baseline)
- [x] Sprint 2:学院系统(任务 · 等级成长 · 等级绑定权限)
  - `User.experience` + 经验阈值自动升级(L0:0 / L1:100 / L2:300 / L3:700,见 `services/leveling.py`)
  - `Task` / `UserTask` 模型;预置 L0→L3 成长主线任务(种子幂等)
  - 接口:`GET /api/v1/tasks`、`GET /api/v1/tasks/{code}`、`POST /api/v1/tasks/{code}/complete`
  - **等级绑定权限**:任务 `min_level` 决定锁定/可完成(403),与 `require_level()` 同源
  - 迁移 `0003_academy`;测试合计 **26 passed**;真库端到端验证通过(完成→升级→闸门)
  - 细节见 `backend/README.md`
- [x] Sprint 3:因子实验室(模板因子 · 组合器)
  - `engine/factor_engine.py` 落地:5 个模板因子(动量/均线/RSI/波动率/均值回归)+ 组合器(标准化加权)+ 确定性样本数据
  - `Factor` 模型(template/stack,JSON spec,版本号);接口:模板目录 / 建模板因子 / 建组合器 / 预览 / 列表 / 删除
  - **等级绑定权限**:模板 L0、组合器 `require_level(L1)`(L0→403,L1→201)
  - 迁移 `0004_factors`;测试合计 **51 passed**(含 engine 纯函数);真库端到端验证通过
  - 计算与 Web 解耦:计算在 `engine/`(纯函数),后端仅持久化与权限
- [x] Sprint 4:回测系统(成本 · 研究报告 · 数据快照 · 异步)
  - engine:`cost_model`(手续费+滑点)+ `backtest`(收益/风险/交易指标+净值)+ `report`(研究报告)
  - 数据 V1:Parquet 存 K 线 + PG 存索引(`MarketDataset`);`DataSnapshot`(内容哈希)保证**可复现**
  - **异步**:`POST /backtests` 入队 → **Celery worker** 计算 → 落库;`GET /backtests/{id}` 轮询
  - 接口:`/datasets`、`/backtests`(创建/列表/详情);迁移 `0005_backtests`
  - 验证:真库 + **真 Celery worker** 端到端(pending→worker 2.2s→success,绑定快照、出研究报告);测试合计 **67 passed**
  - 细节见 `backend/README.md`
- [ ] Sprint 5:科学验证(样本外 · Walk-Forward · 稳健性)

> 环境说明(重要):
> - 本机是 **Windows Server 2019**,Docker Desktop **不支持**(仅支持 Win10/11 客户端),
>   且 WSL2 在 Server 2019 不可用,无法跑 Linux 容器。故改用**原生 PostgreSQL + Redis**(见"本地运行 A")。
> - Docker Compose 路线保留给将来的 **Linux 部署机**(见"本地运行 B")。
> - `alembic.ini` 保持 ASCII:Alembic 以 **OS locale 编码** 读取该 ini,
>   非 UTF-8 主机(Windows GBK)下含中文会触发 `UnicodeDecodeError`。

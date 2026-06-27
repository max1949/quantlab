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
├── models/            # ORM: user · task · factor · market · backtest · validation
├── schemas/           # Pydantic: user · task · factor · backtest · validation
├── services/          # user · task · leveling · factor · market_data · backtest · validation
├── tasks/             # Celery: celery_app · backtest_tasks · validation_tasks
└── auth/              # security.py (hash/JWT) · deps.py (当前用户/等级闸门)
migrations/            # Alembic (0001..0009: baseline/users/academy/factors/backtests/validations/competition/ai/research)
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

## Sprint 5 — 科学验证(样本外 · Walk-Forward · 稳健性)

把"一次回测"升级为"可信验证",抑制过拟合。计算在 `engine/walk_forward.py`,
后端构造在任意切片上算因子信号的闭包(template/stack 通用),异步执行(Celery)。

`Validation`(迁移 `0006`)绑定因子 + 数据快照 + 成本,产出:

- `oos`:样本内/外对比 + 夏普衰减
- `walk_forward`:分段(`n_splits`)逐段回测 + 跨期一致性
- `sensitivity`:模板因子扫窗口参数(组合器退化为单点)
- `robustness`:综合 0–100 评分 + 评级(稳健/中等/偏弱/脆弱)

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/validations` | 创建并运行验证(异步;返回 `pending`/结果) |
| GET | `/api/v1/validations` | 我的验证列表 |
| GET | `/api/v1/validations/{id}` | 验证详情(OOS/WF/敏感性/稳健性) |

## Sprint 6 — 竞技系统(赛季 · 动态评分 · 排行榜)

把"通过科学验证的因子"计入赛季并排名。打分在 `engine/scoring.py`(同步计算,不需 worker):
五维加权(样本外/稳定性/风控/跨品种/研究质量)+ 动态衰减,产出 `final = base × decay`。

- `Season` / `Submission`(迁移 `0007`):一次提交 = 一次成功验证的得分快照(含各维度明细)。
- 提交时**回填 `User.research_score`**(取历史最佳),Sprint 1 预留字段正式启用。
- 赛季创建用 `require_level(L3)` 把关(高级研究员管理);提交对所有登录用户开放。
- 默认赛季种子:`./scripts/seed-season.ps1`(幂等)。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/seasons` | 赛季列表 |
| POST | `/api/v1/seasons` | 创建赛季(需 L3) |
| POST | `/api/v1/seasons/{id}/submissions` | 提交已验证因子 → 算分 |
| GET | `/api/v1/seasons/{id}/leaderboard` | 排行榜(按最终分降序) |
| GET | `/api/v1/seasons/{id}/submissions/me` | 我在该赛季的提交 |

## Sprint 7 — AI 研究助手(研究建议 · 报告总结)

把研究产物喂给**外部 LLM**(OpenAI 兼容,DeepSeek/OpenAI/Moonshot 皆可)生成自然语言复盘。
计算与提示词在 `engine/ai_advisor.py`(纯函数);唯一联网处是 `services/llm_client.py`。

- **可插拔降级**:未配置 `LLM_API_KEY`(或调用失败)时自动改用 engine 本地规则分析,
  接口形状不变,响应里 `source` 标注 `llm` / `local`——**无 Key、无网络也能用且可测**。
- 配置(`.env`):`AI_ENABLED` / `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`。
- `AiInsight`(迁移 `0008`)留存每次生成:最终文本 + 结构化分析 + 来源 + 模型名。
- 只给研究改进建议,**不给买卖信号**。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/ai/status` | 是否已接入 LLM(否则本地降级) |
| POST | `/api/v1/ai/validations/{id}/review` | AI 复盘验证(优点/风险/改进建议) |
| POST | `/api/v1/ai/backtests/{id}/summary` | AI 总结回测研究报告(通俗版) |
| GET | `/api/v1/ai/insights` | 我的 AI 洞察列表 |

## Sprint 8.1 — 研究项目报告(研究生态化)

产品方向从"交易化"转向"研究生态化"(vn.py 推迟为未来可插拔 Execution Adapter)。
第一步:把"因子 + 回测 + 验证"**聚合成一篇人话研究报告**,让小白看到的不再是裸指标。

- 计算在 `engine/research_report.py`(纯函数);`research_service` 取该因子**最新成功的回测 + 验证**聚合。
- `ResearchReport`(迁移 `0009`):标题 / 假设 / 评级 / 阶段完成度 / 完整叙事 / 溯源(backtest_id, validation_id)/ 是否公开。
- 公开报告可被他人查看,为后续**研究员主页 / 研究社区**铺路。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/research/factors/{id}/report` | 为因子生成研究报告(需已有成功回测/验证) |
| GET | `/api/v1/research/reports` | 我的研究报告列表 |
| GET | `/api/v1/research/reports/{id}` | 报告详情(公开报告他人可见) |

## Sprint 8 — 产品化与研究生态(Research OS)

把系统从"研究原型"升级为可被真实小白使用的 MVP,串起完整闭环:
**注册 → 项目 → 因子 → 回测 → 验证 → 报告 → 发布 → 赛季 → 排行榜 → 主页/积分**。
不做实盘/下单/vn.py(推迟为未来可插拔 Execution Adapter)。

迁移 `0010_research_os`:新增 `research_projects` / `research_nodes` / `research_edges` /
`challenges` / `challenge_progress`;`factors` 加 `project_id`;`research_reports` 升级
(`project_id` + `summary/methodology/result/risk_analysis/improvement_suggestion` + `factor_version`)。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST/GET | `/api/v1/projects` | 创建 / 我的研究项目(顶层容器) |
| GET | `/api/v1/projects/{id}` | 项目详情(公开项目他人可见) |
| POST | `/api/v1/projects/{id}/publish` | 发布到研究 Feed(需已有产物) |
| GET | `/api/v1/projects/{id}/graph` | 研究路径图谱(假设→实验→验证→结果) |
| POST | `/api/v1/research/reports/generate` | 生成报告(传 `project_id` 或 `factor_id`) |
| GET | `/api/v1/research/feed` | 研究 Feed(`sort=latest|top`) |
| GET | `/api/v1/researchers/{id}` · `/me` | 研究员主页(统计 + 方向标签) |
| POST | `/api/v1/ai/research-plan` | AI 研究指导(给方向→假设+推荐因子+实验) |
| GET/POST | `/api/v1/challenges` · `/{code}/enroll` · `/{code}/progress` | 30 天研究挑战(自动判定里程碑) |

极简前端单页:后端启动后访问 `http://127.0.0.1:8000/`(详见根目录 `README_PRODUCT.md` / `README_DEVELOPMENT.md`)。

## 测试

```bash
cd backend && pytest          # eager 模式 + 测试库, 不需 worker  (136 passed)
```

覆盖:**Sprint 1** — 注册/登录/`me`/密码哈希/JWT/等级闸门;
**Sprint 2** — 经验升级、任务锁定/完成、`min_level` 403、重复 409;
**Sprint 3** — 模板目录、建因子、参数校验、组合器 L0→403/L1→201、预览;
**Sprint 4** — 数据集、回测成功、指标/研究报告/净值、快照、成本影响、错误分支;
**Sprint 5** — 验证全流程(OOS/WF/敏感性/稳健性)、组合器敏感性退化、错误分支、鉴权;
**Sprint 6** — 赛季创建 L3 闸门、提交算分、排行榜排序、回填 research_score、重复/无效提交、鉴权;
**Sprint 7** — AI 状态、验证复盘/回测总结本地降级、LLM mock 成功、LLM 失败回退本地、错误分支、鉴权;
**Sprint 8.1** — 仅回测/回测+验证生成报告、阶段标记、溯源、无研究 422、公开报告他人可见、鉴权;
**Sprint 8** — 项目创建/因子归属、项目报告 + 显式字段、研究路径图谱(假设→实验→验证→结果)、
发布闸门、研究 Feed、研究员主页统计/方向标签、AI 研究指导(本地)、30 天挑战自动判定、
以及 `test_full_path.py` **完整闭环**(注册→项目→因子→回测→验证→报告→赛季→排行榜→主页→挑战);
**engine** — 因子、成本、回测指标、研究报告、OOS/WF/敏感性/稳健性评分、Research Score 五维 + 衰减、AI 提示词/本地分析(含研究计划)、研究项目报告聚合。

# QuantLab AI

> AI 量化研究员孵化与因子研究平台 —— 量化领域的 **GitHub + Kaggle + 研究员培养系统**。
>
> 本仓库不是"做一个回测网站"。核心资产是 **研究行为数据 + 可复现的研究过程**,目标是沉淀 AI 量化研究基础设施。

当前阶段:**Sprint 9B 产品前端 + Oracle 生产部署**；核心研究链路(Sprint 1–9A)已闭环。

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
7. **vn.py 推迟**:方向修订后聚焦"研究生产线",实盘/下单/vn.py 推迟为未来可插拔 Execution Adapter(非当前核心)。

---

## 技术栈

- 前端:**React + Vite + TailwindCSS**(`frontend-react/`, 生产构建托管于 `/app`)
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
├── frontend-react/         # React SPA (Sprint 9B, 生产前端)
├── frontend/               # Sprint 8 极简 demo (保留于 /app-legacy)
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
| 7 | AI 助手 | 研究建议 · 报告总结(外部 LLM,可降级本地) ✅ |
| 8 | **研究生态化** | 研究报告自动生成 · 研究员主页 · AI 研究 Agent |
| 9+ | Execution Adapter | vn.py / QMT / 模拟盘(可插拔,核心不依赖) |

> **方向修订(Sprint 8)**:核心是「量化研究员生产线 + 研究数据基础设施」,不是交易软件。
> vn.py 推迟为未来的可插拔 **Execution Adapter**(Phase 3),先把研究生态做厚。

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
- [x] Sprint 5:科学验证(样本外 · Walk-Forward · 稳健性)
  - engine `walk_forward.py`:OOS holdout(+衰减)、Walk-Forward 分段一致性、参数敏感性、综合稳健性评分
  - 关键:每段独立用本段数据算信号(**无前视泄漏**),抑制过拟合
  - `Validation` 模型 + 异步(Celery `run_validation_task`)+ `/validations` 路由;迁移 `0006_validations`
  - 验证:真库 + **真 Celery worker** 端到端(动量因子在 RB 上 OOS 夏普 −0.73、稳健性 23.8「脆弱」,正确识别弱因子);测试合计 **81 passed**
  - 细节见 `backend/README.md`
- [x] Sprint 6:竞技系统(赛季 · 动态评分 · 排行榜)
  - engine `scoring.py`:Research Score 五维加权(样本外 30% · 稳定性 25% · 风控 20% · 跨品种 15% · 研究质量 10%)
  - **动态衰减**:`final = base × decay`,衰减由近期(Walk-Forward 末段)表现决定,防止失效老因子霸榜
  - `Season` / `Submission` 模型 + `/seasons`(列表/创建[L3]/提交/排行榜/我的提交);迁移 `0007_competition`
  - 提交时**回填 `User.research_score`**(历史最佳),Sprint 1 预留字段正式启用
  - 验证:真库 + **真 Celery worker** 端到端(动量因子提交得 base 32.26 × decay 0.43 = **final 13.87**,弱因子被正确低估,榜单回填用户积分);测试合计 **93 passed**
  - 细节见 `backend/README.md`
- [x] Sprint 7:AI 研究助手(研究建议 · 报告总结)
  - engine `ai_advisor.py`(纯函数,不联网):LLM 提示词构造 + **确定性本地规则分析**(优点/风险/改进建议)
  - 唯一联网处 `services/llm_client.py`:OpenAI 兼容(DeepSeek/OpenAI/…),**可插拔降级**——无 Key/调用失败自动回退本地分析,接口形状不变
  - `AiInsight` 模型(迁移 `0008`)留存文本 + 结构化分析 + 来源(`llm`/`local`)+ 模型名;接口 `/ai`(status / 验证复盘 / 回测总结 / 洞察列表)
  - 验证:真库 + **真 Celery worker** 端到端(无 Key → `source=local`,AI 正确识别弱动量因子过拟合:衰减 0.59、OOS 夏普 −0.73、跨期一致性 25%);测试合计 **107 passed**
  - 只给研究改进建议,**不给买卖信号**;细节见 `backend/README.md`
- [x] Sprint 8:产品化与研究生态(Research OS;方向从"交易化"转向"研究生产线";vn.py 推迟为可插拔 Execution Adapter)
  - [x] **8.1 研究报告自动生成**:engine `research_report.py` 把「因子+回测+验证」聚合成人话叙事报告
    - `ResearchReport` 模型(迁移 `0009`):标题/假设/评级/阶段完成度/完整叙事/溯源/公开;接口 `/research`(生成/列表/详情)
  - [x] **8.2 Research OS 核心**:`ResearchProject` 顶层容器 + 报告升级(`project_id` + 显式字段)+ **研究路径图谱**(`/projects/{id}/graph`:假设→实验→验证→结果);因子可归入项目
  - [x] **8.3 研究生态面**:研究员主页 `/researchers/{id}`(项目/因子/有效验证/报告数 + 方向标签 + 积分)+ 研究 Feed `/research/feed`(最新/高分)
  - [x] **8.4 AI 研究指导 + 30 天挑战**:`/ai/research-plan`(给方向→假设+推荐因子+实验,不给交易建议)+ `/challenges`(里程碑自动判定:Day1 因子→Day7 OOS→Day15 组合→Day30 报告)
  - [x] **8.5 极简前端单页 + 完整闭环测试 + 产品/开发文档**:`frontend/index.html`(FastAPI 同源托管,`/app/`「一键走完整闭环」)
    - 迁移 `0010_research_os`;新增 `README_PRODUCT.md` / `README_DEVELOPMENT.md`
    - 验证:真库迁移 + 端到端实测(项目报告 final 13.87 回填主页、挑战 3/4、AI 计划本地 3 假设、Feed/图谱完整);测试合计 **136 passed(后端)+ 53 passed(engine)**
- [x] Sprint 9:Growth OS(产品化与自增长;方向锁定"研究人才平台",不接 vn.py)
  - [x] **9A 后端增长内核**:分流/onboarding、研究模板一键开局、分享卡片 + 公开页 `/share/{token}`、关注/关注 Feed、多维榜单(researcher/contributor/newcomer/improved)、邀请裂变(被邀请者首次研究激活发奖)、AI 研究导师 `/ai/mentor/next`、30 天挑战奖励 + 证书、匿名埋点 + 漏斗
    - **两套互不合并的分数**:`reward_points`(游戏激励)与 `research_contribution_score`(研究信用),竞技 `research_score` 仍独立
    - 迁移 `0011_growth_os`(已落真库)+ 种子 `seed-templates`;`test_growth.py` / `test_growth_loop.py` 守护增长闭环;测试合计 **152 passed(后端)+ 53 passed(engine)**
  - [x] **9B React SPA 多页前端**:Landing/登录/工作台/模板库/项目/报告/广场/榜单/挑战/邀请/会员页;FastAPI 同源 `/app`;中英 i18n
  - [x] **9C 生产部署**:Oracle Linux 共存(`q.ziyingke.com`)+ Cloudflare 隧道;脚本见 `docs/oracle-coexist.md`、`scripts/deploy-coexist.sh`
  - [x] **数据同步**:Windows 开发库 → Oracle,`scripts/sync-to-oracle.ps1`(业务表+行情 Parquet+可选前端构建)
- [x] Sprint 10:会员与月卡(不做在线支付)
  - 套餐/权益闸门、`POST /billing/redeem` 兑换码开通;与 ai.ziyingke.com 共用 Supabase 卡密池
  - **刻意不做** `checkout` 在线支付;商业化以**月卡/兑换码**为主
  - 迁移 `0012_membership`;前端 `/pricing` 兑换页

## 产品迭代状态(锁定方向, vn.py/在线支付仍不做)

| 优先级 | 主题 | 状态 |
|---|---|---|
| P0 | 同步流程固化 | ✅ `sync-to-oracle.ps1` · Oracle 更新用 `scripts/update-oracle.sh` |
| P1 | 广场/项目体验打磨 | ✅ Feed 空态/访客横幅 · 项目进度条与下一步高亮 |
| P2 | 学院任务前端露出 | ✅ Dashboard `AcademyTasks` 组件 |
| P3 | 广场 SEO/免登录预览 | ✅ `/api/v1/public/feed` · `/share/{token}` OG 预览页 · `robots.txt` |
| P4 | 运营工具 | ✅ 本地 `generate-redeem-codes.ps1` · 远程 `batch-codes-remote.ps1` · Admin API |
| 远期 | Python 因子沙箱 · Execution Adapter | 进行中: 公式因子+闸门+vn.py 导入 · 沙箱/实盘 Adapter 待续 |

## 生产同步(Windows 开发机 → Oracle)

```powershell
# 在仓库根目录: 导出业务数据 + 上传 + Oracle 导入 + 补种模板/挑战
.\scripts\sync-to-oracle.ps1 -BuildFrontend
```

Oracle 拉代码(私有库需 Deploy Key; **推荐一键脚本**, 避免 `dist/` 与 git 冲突):

```bash
sudo bash /opt/quantlab/scripts/update-oracle.sh
```

等价手动步骤:

```bash
cd /opt/quantlab
GIT_SSH_COMMAND='ssh -i /root/.ssh/quantlab_deploy -o IdentitiesOnly=yes' git fetch origin
git reset --hard origin/master
systemctl restart quantlab
```

仅补业务数据(不动 users):`sudo bash /opt/quantlab/scripts/repair-data-oracle.sh`

> **环境说明(重要):**
> - 本机是 **Windows Server 2019**,Docker Desktop **不支持**(仅支持 Win10/11 客户端),
>   且 WSL2 在 Server 2019 不可用,无法跑 Linux 容器。故改用**原生 PostgreSQL + Redis**(见"本地运行 A")。
> - Docker Compose 路线保留给将来的 **Linux 部署机**(见"本地运行 B")。
> - `alembic.ini` 保持 ASCII:Alembic 以 **OS locale 编码** 读取该 ini,
>   非 UTF-8 主机(Windows GBK)下含中文会触发 `UnicodeDecodeError`。

# QuantLab AI · 开发说明 (README_DEVELOPMENT)

面向开发者:如何在本机把后端 + 异步 worker + 演示前端跑起来,以及如何测试。

## 技术栈

- 后端:Python 3.11 + FastAPI + SQLAlchemy + Alembic
- 异步:Celery + Redis(回测/验证为重计算,走 worker)
- 数据库:PostgreSQL 16(业务/元数据);行情用 Parquet + PG 索引
- 计算引擎:`engine/`(纯函数库,不依赖 Web/DB,便于单测与复用)
- 前端:`frontend/index.html`(零构建静态单页,FastAPI 同源托管)

## 目录结构

```
engine/      纯计算: 因子/回测/成本/验证/评分/AI建议/研究报告 (无副作用, 易测)
backend/     FastAPI 应用: models / schemas / services / api / tasks / migrations / tests
frontend/    极简单页演示 (index.html)
scripts/     PowerShell 启动与种子脚本
data/        行情 Parquet (运行期生成)
```

## 环境准备 (本机 PowerShell, 在仓库根目录)

1. 安装依赖(首次):

```powershell
.\scripts\setup.ps1            # 或: python -m venv .venv; .\.venv\Scripts\pip install -r backend\requirements.txt
```

2. 确认 PostgreSQL / Redis 已作为 Windows 服务运行(本项目用原生安装,非 Docker)。
   连接串见 `backend/app/core/config.py` 与 `.env`(可参考 `.env.example`)。

3. 执行数据库迁移:

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

4. 灌入种子数据(行情 / 赛季 / 30 天挑战):

```powershell
.\scripts\seed-market-data.ps1
.\scripts\seed-season.ps1
.\scripts\seed-challenge.ps1
.\scripts\seed-templates.ps1    # Sprint 9A: 研究模板库 (一键开局)
```

## 启动

开两个终端:

```powershell
# 终端 A: API
.\scripts\run-backend.ps1        # http://127.0.0.1:8000  (Swagger: /docs)

# 终端 B: Celery worker (异步回测/验证)
.\scripts\run-worker.ps1
```

然后浏览器打开 `http://127.0.0.1:8000/`,点「一键走完整研究闭环」。

> 不想起 worker?把 `CELERY_TASK_ALWAYS_EAGER=true` 写进环境/`.env`,任务会在 API 进程内同步执行
> (开发/演示用;生产请用 worker)。

## 测试

```powershell
# 后端 (FastAPI + DB, eager 模式不需 worker)
cd backend
..\.venv\Scripts\python.exe -m pytest

# 引擎纯函数单测
cd ..
.venv\Scripts\python.exe -m pytest engine/tests
```

测试要点:
- `tests/conftest.py` 强制 `celery_task_always_eager=True` 并把行情写入临时目录,互不污染。
- `tests/test_full_path.py` 覆盖完整闭环:注册→项目→因子→回测→验证→报告→赛季→排行榜→主页→挑战。
- 每个模块都有 API 测试;引擎逻辑(因子/回测/验证/评分/报告/AI 计划)均有纯函数单测。

## 数据库迁移规范

- 改 ORM 模型后,新增 `backend/migrations/versions/00XX_*.py`,`down_revision` 指向上一版本。
- 当前最新:`0011_growth_os`(增长字段 + 邀请/模板/分享/关注/埋点 + 挑战奖励证书)。
- 升级:`alembic upgrade head`;回滚:`alembic downgrade -1`。

## AI / LLM 配置 (可选)

`.env` 设置 `AI_ENABLED=true` 与 `LLM_*`(OpenAI 兼容,如 DeepSeek/Moonshot)即可启用外部 LLM;
未配置时所有 AI 接口自动回退到本地确定性规则,功能不缺失。`GET /api/v1/ai/status` 查看当前模式。

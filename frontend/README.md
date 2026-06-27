# frontend — QuantLab AI 极简演示前端

Sprint 8 阶段为**极简单页演示**(零构建、纯静态 `index.html` + 原生 JS),
目的是让人一眼看懂并亲手走完整个 Research OS 闭环:

> 注册 → 创建研究项目 → 创建因子 → 回测 → 科学验证 → 生成研究报告 → 发布 → 提交赛季 → 排行榜 → 研究主页积分

## 打开方式

后端启动后(`.\scripts\run-backend.ps1`),浏览器访问:

```
http://127.0.0.1:8000/         # 自动跳转到 /app/
http://127.0.0.1:8000/app/     # 演示页
```

页面由 FastAPI 的 StaticFiles 直接托管(同源,无需 CORS / 无需 Node 构建)。

## 前置数据(种子)

为了让「回测 / 赛季 / 挑战」可用,先跑一次种子脚本:

```powershell
.\scripts\seed-market-data.ps1   # 行情数据 (回测必需)
.\scripts\seed-season.ps1        # 默认赛季 (排行榜)
.\scripts\seed-challenge.ps1     # 30 天研究挑战
```

> 异步回测/验证需要 Celery worker 在跑;若用单页「一键闭环」,请确保 worker 已启动
> (或后端配置 `CELERY_TASK_ALWAYS_EAGER=true` 同步执行)。

## 未来

正式多页前端(Next.js + React + Tailwind:Dashboard / 工作台 / 报告页 / 研究主页 / 排行榜)
放到后续 Sprint;当前优先把后端闭环与产品流程跑通。

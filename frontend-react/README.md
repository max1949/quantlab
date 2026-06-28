# QuantLab AI 前端 (Sprint 9B)

React SPA, 把后端 Growth OS / Research OS API 包装成"陌生人 5 分钟完成第一次研究"的产品界面。

## 技术栈

- React 18 + TypeScript + **Vite**
- React Router (SPA 路由, basename `/app`)
- Zustand (auth / flow / ui 全局态) + TanStack Query (服务端数据缓存)
- Tailwind CSS
- axios (统一注入 JWT, 401 自动登出)

## 目录

```
src/
  api/        client(axios+拦截器) · endpoints(所有接口) · types
  store/      auth(会话) · flow(研究引导态) · ui(toast)
  components/ Layout · ProtectedRoute · ProfileView · ReportCard · ui
  lib/        nav(后端 stage → 前端路由 映射)
  pages/      Landing/Login/Register/Onboarding/Dashboard/Templates/
              Projects/ProjectDetail/ReportDetail/SharePage/Feed/
              Researcher/MyProfile/Referral/Following/Leaderboards/Challenges
```

## 用户主路径 (landing → share)

落地页 → 注册(带 `?ref` 邀请) → 分流身份 → 工作台"你的下一步" → 模板一键开局
→ 项目页分步引导(回测→验证→报告) → 报告页生成分享卡片 → 公开 `/share/:token`(裂变)。

## 开发

```powershell
# 1. 先起后端 (:8000)
.\scripts\run-backend.ps1
# 2. 起前端开发服务器 (:5173, /api 代理到 :8000, 热更新)
.\scripts\run-frontend-dev.ps1
# 访问 http://127.0.0.1:5173/app/
```

## 构建 / 上线

```powershell
.\scripts\build-frontend.ps1   # 产物 -> frontend-react/dist
```

构建产物 `dist/` 已纳入版本控制, FastAPI 在 `/app` 直接服务
(深层路由如 `/app/projects/123` 由后端 catch-all 回退到 `index.html`)。
服务器只需 `git pull` 即可上线最新前端, 无需安装 Node。

> 旧版 Sprint 8 极简 demo 仍保留在 `/app-legacy`。

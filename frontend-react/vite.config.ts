import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// QuantLab AI 前端 (Sprint 9B)
// - 生产构建产物挂载在 FastAPI 的 /app/ 路径下
// - 开发时把 /api 代理到本地后端 (uvicorn :8000)
export default defineConfig({
  base: "/app/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});

import axios, { AxiosError } from "axios";

// 统一 axios 实例: 自动注入 JWT, 401 自动登出。
export const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
});

const TOKEN_KEY = "ql_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  try {
    const raw = localStorage.getItem("ql-locale");
    if (raw) {
      const loc = JSON.parse(raw)?.state?.locale;
      if (loc === "en" || loc === "zh") {
        config.headers = config.headers ?? {};
        config.headers["Accept-Language"] = loc;
      }
    } else {
      config.headers = config.headers ?? {};
      config.headers["Accept-Language"] = "en";
    }
  } catch {
    config.headers = config.headers ?? {};
    config.headers["Accept-Language"] = "en";
  }
  return config;
});

// 401 时清 token 并跳登录 (在路由守卫里也会兜底)。
let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn;
}

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      setToken(null);
      if (onUnauthorized) onUnauthorized();
    }
    return Promise.reject(error);
  },
);

export function apiErrorMessage(err: unknown, fallback = "请求失败"): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)
      ?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    const status = err.response?.status;
    if (status === 410) {
      return "该功能入口已关闭。请使用正式模拟交易或证据系统。";
    }
    if (status === 403) {
      return "当前账号权限不足，或该功能未解锁。可查看会员页或联系管理员。";
    }
    if (status === 401) {
      return "登录已过期，请重新登录。";
    }
    if (status === 404) {
      return "找不到对应资源，请刷新后重试。";
    }
    if (status === 422) {
      return typeof detail === "string" && detail.trim()
        ? detail
        : "请求未通过业务校验。请检查输入或先完成前置步骤。";
    }
    if (status && status >= 500) {
      return "服务暂时异常。请稍后重试；若持续出现，请联系运维。不会创建真实订单。";
    }
    if (!err.response) {
      return "网络连接失败，请检查网络后重试。";
    }
    // Never surface raw "Request failed with status code NNN" to end users.
    return fallback;
  }
  if (err instanceof Error && err.message && !/status code \d+/i.test(err.message)) {
    return err.message;
  }
  return fallback;
}

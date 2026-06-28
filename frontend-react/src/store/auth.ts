import { create } from "zustand";
import { getToken, setToken } from "../api/client";
import * as ep from "../api/endpoints";
import type { User, UserType } from "../api/types";

interface AuthState {
  token: string | null;
  user: User | null;
  ready: boolean; // 启动时是否已尝试恢复会话
  login: (identifier: string, password: string) => Promise<User>;
  register: (body: {
    email: string;
    username: string;
    password: string;
    user_type?: UserType;
    ref?: string | null;
  }) => Promise<User>;
  logout: () => void;
  refreshMe: () => Promise<User | null>;
  setUser: (user: User) => void;
}

export const useAuth = create<AuthState>((set, get) => ({
  token: getToken(),
  user: null,
  ready: false,

  async login(identifier, password) {
    const tok = await ep.login({ identifier, password });
    setToken(tok.access_token);
    set({ token: tok.access_token });
    const user = await ep.getMe();
    set({ user, ready: true });
    return user;
  },

  async register(body) {
    await ep.register(body);
    // 注册后自动登录
    return get().login(body.email, body.password);
  },

  logout() {
    setToken(null);
    set({ token: null, user: null });
  },

  async refreshMe() {
    if (!getToken()) {
      set({ ready: true });
      return null;
    }
    try {
      const user = await ep.getMe();
      set({ user, ready: true });
      return user;
    } catch {
      setToken(null);
      set({ token: null, user: null, ready: true });
      return null;
    }
  },

  setUser(user) {
    set({ user });
  },
}));

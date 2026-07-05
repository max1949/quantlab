import { create } from "zustand";
import { getToken, setToken } from "../api/client";
import * as ep from "../api/endpoints";
import type { User, UserType } from "../api/types";

interface AuthState {
  token: string | null;
  user: User | null;
  ready: boolean; // 启动时是否已尝试恢复会话
  login: (identifier: string, password: string, captchaToken?: string, captchaAnswer?: string) => Promise<User>;
  register: (body: {
    email: string;
    username: string;
    password: string;
    user_type?: UserType;
    ref?: string | null;
    captcha_token?: string;
    captcha_answer?: string;
  }) => Promise<{ user: User; welcomeEmailHint?: string | null }>;
  loginWithToken: (token: string) => Promise<User>;
  logout: () => void;
  refreshMe: () => Promise<User | null>;
  setUser: (user: User) => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: getToken(),
  user: null,
  ready: false,

  async login(identifier, password, captchaToken?, captchaAnswer?) {
    const tok = await ep.login({
      identifier,
      password,
      captcha_token: captchaToken,
      captcha_answer: captchaAnswer,
    });
    setToken(tok.access_token);
    set({ token: tok.access_token });
    const user = await ep.getMe();
    set({ user, ready: true });
    return user;
  },

  async loginWithToken(token) {
    setToken(token);
    set({ token });
    const user = await ep.getMe();
    set({ user, ready: true });
    return user;
  },

  async register(body) {
    const res = await ep.register(body);
    setToken(res.access_token);
    set({ token: res.access_token, user: res.user, ready: true });
    return { user: res.user, welcomeEmailHint: res.welcome_email_hint ?? null };
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

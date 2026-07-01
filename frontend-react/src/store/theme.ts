import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemePreference = "light" | "dark" | "system";

function resolveDark(preference: ThemePreference): boolean {
  if (preference === "dark") return true;
  if (preference === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function applyTheme(preference: ThemePreference) {
  const dark = resolveDark(preference);
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.style.colorScheme = dark ? "dark" : "light";
}

interface ThemeState {
  preference: ThemePreference;
  setPreference: (p: ThemePreference) => void;
  init: () => void;
}

export const useTheme = create<ThemeState>()(
  persist(
    (set, get) => ({
      preference: "system",
      setPreference: (preference) => {
        applyTheme(preference);
        set({ preference });
      },
      init: () => {
        applyTheme(get().preference);
        if (get().preference !== "system") return;
        const mq = window.matchMedia("(prefers-color-scheme: dark)");
        const handler = () => applyTheme("system");
        mq.addEventListener("change", handler);
      },
    }),
    { name: "ql-theme" }
  )
);

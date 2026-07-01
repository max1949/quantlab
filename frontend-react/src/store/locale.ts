import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Dictionary, Locale } from "../i18n/dictionaries";
import { getDict } from "../i18n/dictionaries";

interface LocaleState {
  locale: Locale;
  dict: Dictionary;
  setLocale: (locale: Locale) => void;
}

export const useLocale = create<LocaleState>()(
  persist(
    (set) => ({
      locale: "en",
      dict: getDict("en"),
      setLocale: (locale) => set({ locale, dict: getDict(locale) }),
    }),
    {
      name: "ql-locale",
      // Only persist locale — dict contains functions that JSON cannot round-trip.
      partialize: (state) => ({ locale: state.locale }),
      merge: (persisted, current) => {
        const locale =
          (persisted as Partial<LocaleState> | undefined)?.locale ?? current.locale;
        return { ...current, locale, dict: getDict(locale) };
      },
    },
  ),
);

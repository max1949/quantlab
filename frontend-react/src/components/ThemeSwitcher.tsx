import { useLocale } from "../store/locale";
import { useTheme, type ThemePreference } from "../store/theme";

const OPTIONS: ThemePreference[] = ["light", "dark", "system"];

export default function ThemeSwitcher() {
  const preference = useTheme((s) => s.preference);
  const setPreference = useTheme((s) => s.setPreference);
  const t = useLocale((s) => s.dict.theme);

  return (
    <div className="flex rounded-lg border border-slate-300 text-xs dark:border-slate-600">
      {OPTIONS.map((opt) => (
        <button
          key={opt}
          type="button"
          title={t[opt]}
          onClick={() => setPreference(opt)}
          className={`px-2 py-1.5 transition ${
            preference === opt
              ? "bg-brand-600 text-white"
              : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
          }`}
        >
          {t[opt]}
        </button>
      ))}
    </div>
  );
}

import { useLocale } from "../store/locale";
import { useTheme, type ThemePreference } from "../store/theme";

const OPTIONS: ThemePreference[] = ["light", "dark", "system"];

/** Compact segmented control: icons + title (no LightDark collision under EN width pressure). */
export default function ThemeSwitcher({ compact = true }: { compact?: boolean }) {
  const preference = useTheme((s) => s.preference);
  const setPreference = useTheme((s) => s.setPreference);
  const t = useLocale((s) => s.dict.theme);

  return (
    <div
      role="group"
      aria-label="Theme"
      className="inline-flex shrink-0 overflow-hidden rounded-lg border border-slate-300 dark:border-slate-600"
    >
      {OPTIONS.map((opt) => {
        const active = preference === opt;
        return (
          <button
            key={opt}
            type="button"
            title={t[opt]}
            aria-label={t[opt]}
            aria-pressed={active}
            onClick={() => setPreference(opt)}
            className={`inline-flex h-8 min-w-7 items-center justify-center gap-1 px-1.5 text-xs transition sm:min-w-8 sm:px-2 ${
              active
                ? "bg-brand-600 text-white"
                : "text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            }`}
          >
            <ThemeIcon preference={opt} />
            {!compact ? <span className="whitespace-nowrap">{t[opt]}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

function ThemeIcon({ preference }: { preference: ThemePreference }) {
  if (preference === "light") {
    return (
      <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true" fill="currentColor">
        <path d="M8 3.5a.75.75 0 0 1 .75-.75h.01a.75.75 0 0 1 0 1.5H8.75A.75.75 0 0 1 8 3.5Zm0 9a.75.75 0 0 1 .75-.75h.01a.75.75 0 0 1 0 1.5H8.75A.75.75 0 0 1 8 12.5ZM3.5 8a.75.75 0 0 1-.75-.75V7.24a.75.75 0 0 1 1.5 0v.01A.75.75 0 0 1 3.5 8Zm9 0a.75.75 0 0 1-.75-.75V7.24a.75.75 0 0 1 1.5 0v.01A.75.75 0 0 1 12.5 8ZM4.93 4.93a.75.75 0 0 1 0-1.06l.01-.01a.75.75 0 1 1 1.06 1.06l-.01.01a.75.75 0 0 1-1.06 0Zm5.07 5.07a.75.75 0 0 1 0-1.06l.01-.01a.75.75 0 1 1 1.06 1.06l-.01.01a.75.75 0 0 1-1.06 0ZM4.93 11.07a.75.75 0 0 1 1.06 0l.01.01a.75.75 0 1 1-1.06 1.06l-.01-.01a.75.75 0 0 1 0-1.06Zm5.07-5.07a.75.75 0 0 1 1.06 0l.01.01a.75.75 0 1 1-1.06 1.06l-.01-.01a.75.75 0 0 1 0-1.06ZM8 5.5A2.5 2.5 0 1 0 8 10.5 2.5 2.5 0 0 0 8 5.5Z" />
      </svg>
    );
  }
  if (preference === "dark") {
    return (
      <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true" fill="currentColor">
        <path d="M7.2 1.4a.7.7 0 0 1 .2 1.37A5.1 5.1 0 1 0 12.8 9.2a.7.7 0 0 1 1.36.28A6.5 6.5 0 1 1 7.2 1.4Z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true" fill="currentColor">
      <path d="M2.5 3.5A1.5 1.5 0 0 1 4 2h8a1.5 1.5 0 0 1 1.5 1.5v6A1.5 1.5 0 0 1 12 11H4a1.5 1.5 0 0 1-1.5-1.5v-6ZM4 12.5h8a.75.75 0 0 1 0 1.5H4a.75.75 0 0 1 0-1.5Z" />
    </svg>
  );
}

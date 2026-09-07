import { useLocale } from "../store/locale";

export default function LanguageSwitcher() {
  const locale = useLocale((s) => s.locale);
  const setLocale = useLocale((s) => s.setLocale);

  return (
    <div
      role="group"
      aria-label="Language"
      className="inline-flex shrink-0 overflow-hidden rounded-lg border border-slate-300 dark:border-slate-600"
    >
      <button
        type="button"
        aria-pressed={locale === "en"}
        onClick={() => setLocale("en")}
        className={`inline-flex h-8 items-center px-2 text-xs font-medium transition sm:px-2.5 ${
          locale === "en"
            ? "bg-brand-600 text-white"
            : "text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        aria-pressed={locale === "zh"}
        onClick={() => setLocale("zh")}
        className={`inline-flex h-8 items-center px-2 text-xs font-medium transition sm:px-2.5 ${
          locale === "zh"
            ? "bg-brand-600 text-white"
            : "text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        }`}
      >
        中文
      </button>
    </div>
  );
}

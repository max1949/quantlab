import { useLocale } from "../store/locale";

export default function LanguageSwitcher() {
  const locale = useLocale((s) => s.locale);
  const setLocale = useLocale((s) => s.setLocale);

  return (
    <div className="flex rounded-lg border border-slate-300 text-xs dark:border-slate-600">
      <button
        type="button"
        onClick={() => setLocale("en")}
        className={`px-2.5 py-1.5 transition ${
          locale === "en"
            ? "bg-brand-600 text-white"
            : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLocale("zh")}
        className={`px-2.5 py-1.5 transition ${
          locale === "zh"
            ? "bg-brand-600 text-white"
            : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
        }`}
      >
        中文
      </button>
    </div>
  );
}

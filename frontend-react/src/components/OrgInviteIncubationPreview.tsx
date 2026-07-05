import { Link } from "react-router-dom";
import HandbookExportButtons from "./HandbookExportButtons";
import { useLocale } from "../store/locale";

export default function OrgInviteIncubationPreview() {
  const t = useLocale((s) => s.dict.orgInviteIncubation);

  return (
    <div className="mt-6 rounded-xl border border-indigo-200 bg-gradient-to-r from-indigo-50/80 to-brand-50/50 p-4 dark:border-indigo-900 dark:from-indigo-950/40 dark:to-brand-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
        🎓 {t.badge}
      </p>
      <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{t.title}</p>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t.subtitle}</p>
      <ol className="mt-3 list-inside list-decimal space-y-1 text-sm text-slate-600 dark:text-slate-300">
        {t.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <HandbookExportButtons compact />
        <Link to="/handbook" className="btn text-xs">
          {t.handbookCta}
        </Link>
      </div>
    </div>
  );
}

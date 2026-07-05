import { Link } from "react-router-dom";
import type { ReportDetail } from "../api/types";
import { primaryTemplateForSymbol } from "../lib/templateHints";
import { FOLLOWING_REPORT_HANDOFF_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

type Props = {
  report: ReportDetail;
};

export default function FollowingReportHandoffPanel({ report }: Props) {
  const d = useLocale((s) => s.dict.followingReportHandoff);
  const rd = useLocale((s) => s.dict.reportDiscover);
  const show =
    typeof window !== "undefined" && sessionStorage.getItem(FOLLOWING_REPORT_HANDOFF_KEY) === report.id;

  if (!show) return null;

  const templateCode = primaryTemplateForSymbol(report.symbol);
  const templateTitle = templateCode
    ? rd.templateNames[templateCode as keyof typeof rd.templateNames]
    : null;
  const templatesPath = templateCode ? `/templates?focus=${templateCode}` : "/templates";

  const dismiss = () => sessionStorage.removeItem(FOLLOWING_REPORT_HANDOFF_KEY);

  return (
    <div className="mb-4 card border border-teal-200 bg-gradient-to-r from-teal-50/90 to-cyan-50/60 dark:border-teal-900 dark:from-teal-950/40 dark:to-cyan-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-teal-800 dark:text-teal-200">
        📖 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message(report.symbol)}</p>
      <p className="mt-2 text-xs text-teal-900/80 dark:text-teal-100/80">
        {templateTitle ? d.templateHint(templateTitle) : d.genericHint}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to={templatesPath} className="btn-primary text-xs" onClick={dismiss}>
          {d.startTemplate}
        </Link>
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

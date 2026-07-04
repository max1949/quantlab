import { Link } from "react-router-dom";
import type { ReportSummary } from "../api/types";
import { useLocale } from "../store/locale";
import { GradeBadge } from "./ui";

export default function ReportCard({ report }: { report: ReportSummary }) {
  const { dict } = useLocale();
  const rc = dict.reportCard;

  return (
    <div className="card flex h-full flex-col hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <Link to={`/reports/${report.id}`} className="min-w-0 flex-1">
          <h3 className="font-semibold text-slate-800 hover:text-brand-600 dark:text-slate-100">
            {report.title}
          </h3>
        </Link>
        <GradeBadge grade={report.grade} />
      </div>
      {(report.paper_graduated || report.paper_tracking) && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {report.paper_graduated && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
              {rc.badgePaperGraduated}
            </span>
          )}
          {report.paper_tracking && (
            <span className="rounded-full bg-brand-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-800 dark:bg-brand-950 dark:text-brand-200">
              {rc.badgePaperTracking}
            </span>
          )}
        </div>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <span className="badge">{report.symbol}</span>
        {report.timeframe && (
          <span>
            {rc.timeframe}: {report.timeframe}
          </span>
        )}
        {report.factor_kind && (
          <span className="badge">{rc.factorKind(report.factor_kind)}</span>
        )}
        {report.factor_template && (
          <span className="badge">{report.factor_template}</span>
        )}
        {report.oos_sharpe != null && (
          <span>
            {rc.oosSharpe}: {report.oos_sharpe.toFixed(2)}
          </span>
        )}
        {report.robustness_score != null && (
          <span>
            {rc.robustness}: {report.robustness_score.toFixed(0)}
          </span>
        )}
        <span>{new Date(report.created_at).toLocaleDateString()}</span>
      </div>
      <div className="mt-auto flex items-center justify-between pt-3 text-sm">
        <Link to={`/reports/${report.id}`} className="font-medium text-brand-600 hover:underline">
          {rc.readFull} →
        </Link>
        <Link to={`/u/${report.owner_id}`} className="text-xs text-slate-500 hover:text-brand-600">
          {rc.viewResearcher}
        </Link>
      </div>
    </div>
  );
}

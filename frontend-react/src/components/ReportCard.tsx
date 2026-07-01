import { Link } from "react-router-dom";
import type { ReportSummary } from "../api/types";
import { useLocale } from "../store/locale";
import { GradeBadge } from "./ui";

export default function ReportCard({ report }: { report: ReportSummary }) {
  const { dict } = useLocale();
  return (
    <Link to={`/reports/${report.id}`} className="card block hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-slate-800">{report.title}</h3>
        <GradeBadge grade={report.grade} />
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
        <span className="badge">{report.symbol}</span>
        <Link
          to={`/u/${report.owner_id}`}
          className="text-brand-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {dict.reportCard.viewResearcher}
        </Link>
        <span>{new Date(report.created_at).toLocaleDateString()}</span>
      </div>
    </Link>
  );
}

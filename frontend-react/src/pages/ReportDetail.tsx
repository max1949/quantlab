import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getReportForViewer } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { ErrorBox, GradeBadge, PageTitle, Spinner } from "../components/ui";
import ReplicationReportHandoffPanel from "../components/ReplicationReportHandoffPanel";
import ReportPublishCoach from "../components/ReportPublishCoach";
import FollowingReportHandoffPanel from "../components/FollowingReportHandoffPanel";
import ReportDiscoverPanel from "../components/ReportDiscoverPanel";
import ReportShareCoach from "../components/ReportShareCoach";
import FirstReportCoachPanel from "../components/FirstReportCoachPanel";

export default function ReportDetail() {
  const { dict } = useLocale();
  const t = dict.report;
  const { id = "" } = useParams();
  const user = useAuth((s) => s.user);

  const report = useQuery({
    queryKey: ["report", id, Boolean(user)],
    queryFn: () => getReportForViewer(id, Boolean(user)),
  });

  const isOwner = Boolean(user && report.data && report.data.owner_id === user.id);

  if (report.isLoading) return <Spinner />;
  if (report.isError)
    return <ErrorBox message={apiErrorMessage(report.error, t.notFound)} />;

  const r = report.data!;

  const sections: { title: string; body: string }[] = [
    { title: t.hypothesis, body: r.hypothesis },
    { title: t.methodology, body: r.methodology },
    { title: t.result, body: r.result },
    { title: t.risk, body: r.risk_analysis },
    { title: t.improvement, body: r.improvement_suggestion },
  ];

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title={r.title} subtitle={r.summary} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <GradeBadge grade={r.grade} />
        <span className="badge">
          {t.symbol} {r.symbol}
        </span>
        <span className="badge">{t.factorVersion(r.factor_version)}</span>
        {r.project_id && isOwner && (
          <Link to={`/projects/${r.project_id}`} className="badge text-brand-600">
            {t.backToProject}
          </Link>
        )}
        {!user && (
          <Link to="/register" className="badge text-brand-600">
            {t.guestCta}
          </Link>
        )}
      </div>

      {isOwner && <FirstReportCoachPanel placement="report" reportId={id} />}

      {isOwner && (
        <ReplicationReportHandoffPanel reportId={id} projectId={r.project_id} />
      )}

      {!isOwner && <FollowingReportHandoffPanel report={r} />}

      {!isOwner && <ReportDiscoverPanel report={r} />}

      {isOwner && r.project_id && (
        <div id="report-publish">
          <ReportPublishCoach projectId={r.project_id} />
        </div>
      )}

      <div className="space-y-4">
        {sections
          .filter((s) => s.body)
          .map((s) => (
            <div key={s.title} className="card">
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">{s.title}</h3>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                {s.body}
              </p>
            </div>
          ))}
      </div>

      {isOwner && <ReportShareCoach reportId={id} />}
    </div>
  );
}

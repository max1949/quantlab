import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getReportForViewer, shareReport, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { academyRewardMessage } from "../lib/academy";
import { ErrorBox, GradeBadge, PageTitle, Spinner } from "../components/ui";
import ReportPublishCoach from "../components/ReportPublishCoach";
import ReportDiscoverPanel from "../components/ReportDiscoverPanel";

export default function ReportDetail() {
  const { dict } = useLocale();
  const t = dict.report;
  const d = dict.dashboard;
  const { id = "" } = useParams();
  const user = useAuth((s) => s.user);
  const refreshMe = useAuth((s) => s.refreshMe);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const report = useQuery({
    queryKey: ["report", id, Boolean(user)],
    queryFn: () => getReportForViewer(id, Boolean(user)),
  });

  const isOwner = Boolean(user && report.data && report.data.owner_id === user.id);

  const share = useMutation({
    mutationFn: () => shareReport(id),
    onSuccess: async (res) => {
      void trackEvent("share_created", { report: id });
      const url = `${window.location.origin}/share/${res.token}`;
      setShareUrl(url);
      notify(t.shareCreated, "success");
      const msg = academyRewardMessage(res.academy_rewards, d.academyXpEarned);
      if (msg) notify(msg, "success");
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      await refreshMe();
    },
    onError: (e) => notify(apiErrorMessage(e, t.shareFail), "error"),
  });

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

  async function copyLink() {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    notify(t.copied, "success");
  }

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

      {!isOwner && <ReportDiscoverPanel report={r} />}

      {isOwner && r.project_id && <ReportPublishCoach projectId={r.project_id} />}

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

      {isOwner && (
        <div className="mt-6 card bg-brand-50/40 dark:bg-brand-950/20">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">📣 {t.shareTitle}</h3>
          <p className="mt-1 text-sm text-slate-500">{t.shareDesc}</p>
          {shareUrl ? (
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input className="input flex-1" value={shareUrl} readOnly />
              <button className="btn-primary" onClick={copyLink}>
                {t.copyLink}
              </button>
              <a className="btn-ghost" href={shareUrl} target="_blank" rel="noreferrer">
                {t.preview}
              </a>
            </div>
          ) : (
            <button
              className="btn-primary mt-3"
              disabled={share.isPending}
              onClick={() => share.mutate()}
            >
              {share.isPending ? t.shareGenerating : t.shareGenerate}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import type { ReportDetail } from "../api/types";
import { getResearcher, trackEvent } from "../api/endpoints";
import { armFollowingTemplateHandoff, buildTemplatesHandoffPath, primaryTemplateForSymbol } from "../lib/templateHints";
import { replicationBenchmarkFromReport, savePendingReplicationBenchmark } from "../lib/replicationBenchmark";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import ResearcherFollowButton from "./ResearcherFollowButton";
import { Spinner } from "./ui";

type Props = {
  report: ReportDetail;
};

export default function ReportDiscoverPanel({ report }: Props) {
  const user = useAuth((s) => s.user);
  const { dict } = useLocale();
  const t = dict.reportDiscover;
  const p = dict.profile;

  const templateCode = primaryTemplateForSymbol(report.symbol);
  const templateTitle = templateCode ? t.templateNames[templateCode as keyof typeof t.templateNames] : null;
  const templatesPath = buildTemplatesHandoffPath(report.symbol, templateCode);

  const researcher = useQuery({
    queryKey: ["researcher", report.owner_id],
    queryFn: () => getResearcher(report.owner_id),
  });

  if (researcher.isLoading) return <Spinner />;

  const prof = researcher.data;
  const isSelf = user?.id === report.owner_id;

  return (
    <div className="mb-6 grid gap-4 lg:grid-cols-2">
      <div className="card border-slate-200 bg-slate-50/60 dark:border-slate-700 dark:bg-slate-900/40">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{t.authorTitle}</p>
        {prof ? (
          <div className="mt-3 flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700 dark:bg-brand-900 dark:text-brand-200">
                {prof.username.slice(0, 2).toUpperCase()}
              </span>
              <div className="min-w-0">
                <p className="truncate font-semibold text-slate-800 dark:text-slate-100">{prof.username}</p>
                <p className="text-xs text-slate-500">
                  {prof.level_label} · {p.followers} {prof.followers}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
              <Link
                to={`/u/${report.owner_id}`}
                className="btn-ghost text-xs"
                onClick={() => void trackEvent("report_discover_profile", { owner_id: report.owner_id })}
              >
                {t.viewProfile}
              </Link>
              {!isSelf &&
                (user ? (
                  <ResearcherFollowButton
                    ownerId={report.owner_id}
                    isFollowing={prof.is_following}
                    reportId={report.id}
                    followEvent="report_discover_follow"
                    unfollowEvent="report_discover_unfollow"
                  />
                ) : (
                  <Link
                    to="/login"
                    state={{ from: `/reports/${report.id}` }}
                    className="btn-primary text-xs"
                    onClick={() => void trackEvent("report_discover_follow_login", { report_id: report.id })}
                  >
                    {t.followLogin}
                  </Link>
                ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="card border-brand-100 bg-brand-50/50 dark:border-brand-900 dark:bg-brand-950/30">
        <p className="text-xs font-medium uppercase tracking-wide text-brand-600 dark:text-brand-300">
          {t.tryTemplate}
        </p>
        <h3 className="mt-2 font-semibold text-slate-800 dark:text-slate-100">
          {templateTitle ?? t.genericTemplateTitle(report.symbol)}
        </h3>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          {t.tryTemplateDesc(report.symbol)}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {user ? (
            <Link
              to={templatesPath}
              className="btn-primary text-sm"
              onClick={() => {
                void trackEvent("report_discover_template", {
                  report_id: report.id,
                  symbol: report.symbol,
                  template: templateCode,
                });
                armFollowingTemplateHandoff(report.symbol);
                savePendingReplicationBenchmark(replicationBenchmarkFromReport(report));
              }}
            >
              {t.startTemplate}
            </Link>
          ) : (
            <>
              <Link
                to="/register"
                className="btn-primary text-sm"
                onClick={() =>
                  void trackEvent("report_discover_register", {
                    report_id: report.id,
                    symbol: report.symbol,
                    template: templateCode,
                  })
                }
              >
                {t.registerCta}
              </Link>
              <Link
                to="/login"
                state={{ from: templatesPath }}
                className="btn-ghost text-sm"
              >
                {t.loginCta}
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

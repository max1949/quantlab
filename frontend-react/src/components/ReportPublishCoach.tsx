import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getProject, getProjectQuality, publishProject, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { academyRewardMessage } from "../lib/academy";
import { burstConfetti } from "../lib/confetti";
import {
  REPLICATION_FLOW_REPORT_KEY,
  REPLICATION_PUBLISH_FEED_KEY,
  REPLICATION_REPORT_WELCOME_KEY,
} from "../lib/onboardingFocus";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

type Props = {
  projectId: string;
  reportId?: string;
};

export default function ReportPublishCoach({ projectId, reportId }: Props) {
  const t = useLocale((s) => s.dict.report);
  const rp = useLocale((s) => s.dict.replicationPublishCoach);
  const d = useLocale((s) => s.dict.dashboard);
  const atl = useLocale((s) => s.dict.academyTaskLabels);
  const pd = useLocale((s) => s.dict.projectDetail);
  const notify = useUi((s) => s.notify);
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);
  const qc = useQueryClient();

  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });
  const quality = useQuery({
    queryKey: ["project-quality", projectId],
    queryFn: () => getProjectQuality(projectId),
    enabled: Boolean(projectId),
  });

  const publish = useMutation({
    mutationFn: () => publishProject(projectId),
    onSuccess: async (res) => {
      void trackEvent("project_published", { project: projectId, from: "report" });
      notify(pd.publishDone, "success");
      const msg = academyRewardMessage(res.academy_rewards, d.academyXpEarned, atl);
      if (msg) notify(msg, "success");
      void qc.invalidateQueries({ queryKey: ["project", projectId] });
      void qc.invalidateQueries({ queryKey: ["project-quality", projectId] });
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
      const me = await useAuth.getState().refreshMe();
      if (me) setUser(me);
      const replicationFlow =
        reportId &&
        (sessionStorage.getItem(REPLICATION_FLOW_REPORT_KEY) === reportId ||
          sessionStorage.getItem(REPLICATION_REPORT_WELCOME_KEY) === reportId);
      if (replicationFlow && reportId) {
        sessionStorage.removeItem(REPLICATION_REPORT_WELCOME_KEY);
        sessionStorage.removeItem(REPLICATION_FLOW_REPORT_KEY);
        sessionStorage.setItem(REPLICATION_PUBLISH_FEED_KEY, reportId);
        burstConfetti(2800);
        notify(rp.publishedToast, "success");
        void trackEvent("replication_published", { report_id: reportId, project_id: projectId });
        window.setTimeout(() => navigate(`/feed?highlight=${reportId}`), 600);
      }
    },
    onError: (e) => notify(apiErrorMessage(e, pd.publishFail), "error"),
  });

  if (project.isLoading || !project.data) return null;

  if (project.data.status === "published") {
    const replicationLive =
      reportId && typeof window !== "undefined"
        ? sessionStorage.getItem(REPLICATION_PUBLISH_FEED_KEY) === reportId
        : false;
    const feedHref = reportId ? `/feed?highlight=${reportId}` : "/feed";

    return (
      <div className="mb-6 card border border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/30">
        <p className="font-semibold text-emerald-800 dark:text-emerald-200">
          {replicationLive ? rp.publishedTitle : t.publishedTitle}
        </p>
        <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-300">
          {replicationLive ? rp.publishedDesc : t.publishedDesc}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {replicationLive && reportId ? (
            <>
              <Link to={feedHref} className="btn-primary">
                {rp.viewOnFeed}
              </Link>
              <a href="#report-share" className="btn">
                {t.publishedShareNext}
              </a>
            </>
          ) : (
            <>
              <a href="#report-share" className="btn-primary">
                {t.publishedShareNext}
              </a>
              <Link to="/feed" className="btn-ghost">
                {t.viewFeed}
              </Link>
            </>
          )}
        </div>
      </div>
    );
  }

  const canPublish = quality.data?.passed === true;

  return (
    <div
      className={`mb-6 card border ${
        canPublish
          ? "border-brand-200 bg-brand-50/50 dark:border-brand-900 dark:bg-brand-950/30"
          : "border-amber-200 bg-amber-50/40 dark:border-amber-900 dark:bg-amber-950/20"
      }`}
    >
      <p className="font-semibold text-slate-800 dark:text-slate-100">{t.publishNextTitle}</p>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{t.publishNextDesc}</p>

      {!canPublish && quality.data && quality.data.reasons.length > 0 && (
        <ul className="mt-3 list-inside list-disc text-sm text-amber-800 dark:text-amber-200">
          {quality.data.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {canPublish ? (
          <button
            type="button"
            className="btn-primary"
            disabled={publish.isPending}
            onClick={() => publish.mutate()}
          >
            {publish.isPending ? pd.publishProject + "…" : t.publishNow}
          </button>
        ) : (
          <Link to={`/projects/${projectId}`} className="btn-primary">
            {t.backToFix}
          </Link>
        )}
        <Link to={`/projects/${projectId}`} className="btn-ghost">
          {t.backToProject}
        </Link>
      </div>
    </div>
  );
}

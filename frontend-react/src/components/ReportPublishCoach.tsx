import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getProject, getProjectQuality, publishProject, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { academyRewardMessage } from "../lib/academy";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

type Props = {
  projectId: string;
};

export default function ReportPublishCoach({ projectId }: Props) {
  const t = useLocale((s) => s.dict.report);
  const d = useLocale((s) => s.dict.dashboard);
  const pd = useLocale((s) => s.dict.projectDetail);
  const notify = useUi((s) => s.notify);
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
      const msg = academyRewardMessage(res.academy_rewards, d.academyXpEarned);
      if (msg) notify(msg, "success");
      void qc.invalidateQueries({ queryKey: ["project", projectId] });
      void qc.invalidateQueries({ queryKey: ["project-quality", projectId] });
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
      const me = await useAuth.getState().refreshMe();
      if (me) setUser(me);
    },
    onError: (e) => notify(apiErrorMessage(e, pd.publishFail), "error"),
  });

  if (project.isLoading || !project.data) return null;

  if (project.data.status === "published") {
    return (
      <div className="mb-6 card border border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/30">
        <p className="font-semibold text-emerald-800 dark:text-emerald-200">{t.publishedTitle}</p>
        <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-300">{t.publishedDesc}</p>
        <Link to="/feed" className="btn-primary mt-3 inline-block">
          {t.viewFeed}
        </Link>
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

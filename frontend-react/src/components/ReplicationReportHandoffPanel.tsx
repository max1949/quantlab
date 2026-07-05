import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { burstConfetti } from "../lib/confetti";
import { REPLICATION_REPORT_WELCOME_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

function handoffDismissKey(reportId: string) {
  return `quantlab-replication-report-handoff-dismissed-${reportId}`;
}

type Props = {
  reportId: string;
  projectId: string | null;
};

export default function ReplicationReportHandoffPanel({ reportId, projectId }: Props) {
  const d = useLocale((s) => s.dict.replicationReportHandoff);
  const welcome =
    typeof window !== "undefined" && sessionStorage.getItem(REPLICATION_REPORT_WELCOME_KEY) === reportId;
  const [dismissed, setDismissed] = useState(
    () => typeof window !== "undefined" && localStorage.getItem(handoffDismissKey(reportId)) === "1",
  );
  const show = welcome && !dismissed;

  useEffect(() => {
    if (!show) return;
    burstConfetti(2600);
  }, [show]);

  if (!show) return null;

  const dismiss = () => {
    localStorage.setItem(handoffDismissKey(reportId), "1");
    setDismissed(true);
  };

  return (
    <div className="mb-4 card border border-violet-200 bg-gradient-to-r from-violet-50/90 to-indigo-50/60 dark:border-violet-900 dark:from-violet-950/40 dark:to-indigo-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-violet-800 dark:text-violet-200">
        🎓 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <p className="mt-2 text-xs text-violet-900/80 dark:text-violet-100/80">{d.hint}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {projectId && (
          <a href="#report-publish" className="btn-primary text-xs">
            {d.publish}
          </a>
        )}
        <a href="#report-share" className="btn text-xs">
          {d.share}
        </a>
        <Link to="/me/following" className="btn text-xs" onClick={dismiss}>
          {d.backToFollowing}
        </Link>
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

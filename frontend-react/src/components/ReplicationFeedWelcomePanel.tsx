import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { burstConfetti } from "../lib/confetti";
import { REPLICATION_PUBLISH_FEED_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

export default function ReplicationFeedWelcomePanel() {
  const d = useLocale((s) => s.dict.replicationFeedWelcome);
  const [params] = useSearchParams();
  const highlightId = params.get("highlight");
  const show =
    typeof window !== "undefined" &&
    Boolean(highlightId) &&
    sessionStorage.getItem(REPLICATION_PUBLISH_FEED_KEY) === highlightId;

  useEffect(() => {
    if (!show) return;
    burstConfetti(2200);
  }, [show]);

  if (!show || !highlightId) return null;

  const dismiss = () => sessionStorage.removeItem(REPLICATION_PUBLISH_FEED_KEY);

  return (
    <div className="mb-4 card border border-violet-200 bg-gradient-to-r from-violet-50/90 to-emerald-50/60 dark:border-violet-900 dark:from-violet-950/40 dark:to-emerald-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-violet-800 dark:text-violet-200">
        🎓 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to={`/reports/${highlightId}#report-share`} className="btn-primary text-xs">
          {d.createShare}
        </Link>
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

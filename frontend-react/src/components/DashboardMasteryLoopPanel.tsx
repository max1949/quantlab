import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";
import { useLocale } from "../store/locale";

const DISMISS_KEY = "quantlab-dashboard-mastery-loop-dismissed";

export default function DashboardMasteryLoopPanel() {
  const d = useLocale((s) => s.dict.dashboardMasteryLoop);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const following = journey.data?.social_following_count ?? 0;
  const coach = journey.data?.share_growth_coaching;
  const hasShare = Boolean(coach);

  const matches = !dismissed && following >= NETWORK_FOLLOW_TARGET && !journey.isLoading;

  if (!matches) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="card border border-indigo-200 bg-gradient-to-r from-indigo-50/80 to-violet-50/50 dark:border-indigo-900 dark:from-indigo-950/40 dark:to-violet-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
        🔁 {d.badge}
      </p>
      <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <ol className="mt-3 grid gap-2 text-xs sm:grid-cols-4">
        {d.steps.map((step, index) => (
          <li
            key={step}
            className="rounded-lg border border-indigo-200/80 bg-white/70 px-2.5 py-2 dark:border-indigo-900 dark:bg-slate-900/50"
          >
            <span className="font-bold text-indigo-700 dark:text-indigo-300">{index + 1}</span>
            <span className="ml-1.5 text-slate-700 dark:text-slate-200">{step}</span>
          </li>
        ))}
      </ol>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/me/following" className="btn-primary text-xs">
          {d.openFollowing}
        </Link>
        <Link to="/feed?focus=follow" className="btn text-xs">
          {d.browseFeed}
        </Link>
        {hasShare && coach && (
          <Link to={coach.share_url_path} className="btn text-xs">
            {d.shareGrowth}
          </Link>
        )}
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

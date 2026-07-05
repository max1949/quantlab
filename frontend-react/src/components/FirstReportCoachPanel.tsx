import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

const DISMISS_KEY = "quantlab-first-report-dismissed";

export default function FirstReportCoachPanel() {
  const d = useLocale((s) => s.dict.firstReportCoach);
  const stages = useLocale((s) => s.dict.stages);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  if (dismissed) return null;
  if (journey.isLoading) return null;
  const coach = journey.data?.first_report_coaching;
  if (!coach) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="card border border-amber-200 bg-gradient-to-r from-amber-50/90 to-orange-50/50 dark:border-amber-900 dark:from-amber-950/40 dark:to-orange-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
            {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          <p className="mt-2 text-sm text-amber-900/90 dark:text-amber-100/90">{coach.message}</p>
          <p className="mt-2 text-xs text-amber-800/80 dark:text-amber-200/80">
            {d.unlocked(coach.unlock_features)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs">
            {ctaLabel}
          </Link>
          <Link to="/leaderboards/paper_mastery" className="btn whitespace-nowrap text-xs">
            {d.viewBoard}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

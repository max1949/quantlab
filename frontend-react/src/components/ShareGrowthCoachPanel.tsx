import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

const DISMISS_KEY = "quantlab-share-growth-coach-dismissed";

export default function ShareGrowthCoachPanel() {
  const d = useLocale((s) => s.dict.shareGrowthCoach);
  const notify = useUi((s) => s.notify);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const coach = journey.data?.share_growth_coaching;

  if (dismissed || journey.isLoading || !coach) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  const copyLink = async () => {
    const url = `${window.location.origin}${coach.share_url_path}`;
    await navigator.clipboard.writeText(url);
    notify(d.copied, "success");
  };

  return (
    <div className="card border border-emerald-200 bg-gradient-to-r from-emerald-50/90 to-teal-50/50 dark:border-emerald-900 dark:from-emerald-950/40 dark:to-teal-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
            {coach.badge}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100">
              {d.views(coach.views)}
            </span>
            <span className="rounded-full bg-teal-100 px-2.5 py-1 text-xs font-medium text-teal-900 dark:bg-teal-950/50 dark:text-teal-100">
              {d.followers(coach.followers)}
            </span>
            <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-xs font-medium text-cyan-900 dark:bg-cyan-950/50 dark:text-cyan-100">
              {d.following(coach.following)}
            </span>
          </div>
          {coach.report_title && (
            <p className="mt-2 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.report_title}</p>
          )}
          <p className="mt-2 text-sm text-emerald-900/90 dark:text-emerald-100/90">{coach.message}</p>

          <div className="mt-4 rounded-lg border border-emerald-300/50 bg-white/60 p-3 dark:border-emerald-800 dark:bg-slate-900/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
              {coach.guide_title}
            </p>
            <ol className="mt-3 grid gap-2 sm:grid-cols-3">
              {coach.guide_steps.map((step) => (
                <li
                  key={step.step}
                  className="rounded-lg border border-emerald-200 bg-emerald-50/80 px-2.5 py-2 dark:border-emerald-900 dark:bg-emerald-950/30"
                >
                  <div className="flex items-start gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-xs font-bold text-white">
                      {step.step}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-emerald-950 dark:text-emerald-50">
                        {step.label}
                      </p>
                      <p className="mt-1 text-[11px] leading-snug text-emerald-900/80 dark:text-emerald-100/80">
                        {step.hint}
                      </p>
                      <Link
                        to={step.cta_path}
                        className="mt-2 inline-block text-[10px] font-semibold text-brand-600 hover:underline dark:text-brand-400"
                      >
                        {d.stepGo}
                      </Link>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.feed_path} className="btn-primary whitespace-nowrap text-xs">
            {d.viewFeed}
          </Link>
          <Link to={coach.profile_path} className="btn whitespace-nowrap text-xs">
            {d.viewProfile}
          </Link>
          {coach.following > 0 && (
            <Link to={coach.following_feed_path} className="btn whitespace-nowrap text-xs">
              {d.viewFollowing}
            </Link>
          )}
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={copyLink}>
            {d.copyLink}
          </button>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

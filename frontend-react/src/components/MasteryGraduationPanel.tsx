import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { burstConfetti } from "../lib/confetti";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { stageToCtaLabel } from "../lib/nav";
import HandbookExportButtons from "./HandbookExportButtons";

const DISMISS_KEY = "quantlab-mastery-graduation-dismissed";
const CONFETTI_KEY = "quantlab-mastery-graduation-confetti";

export default function MasteryGraduationPanel() {
  const d = useLocale((s) => s.dict.masteryGraduation);
  const stages = useLocale((s) => s.dict.stages);
  const notify = useUi((s) => s.notify);
  const rootRef = useRef<HTMLDivElement>(null);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");
  const [highlighted, setHighlighted] = useState(false);

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const coach = journey.data?.mastery_graduation_coaching;

  useEffect(() => {
    if (!coach || localStorage.getItem(CONFETTI_KEY) === "1") return;
    burstConfetti(3600);
    localStorage.setItem(CONFETTI_KEY, "1");
    const scrollTimer = window.setTimeout(() => {
      rootRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      setHighlighted(true);
    }, 150);
    const clearTimer = window.setTimeout(() => setHighlighted(false), 3500);
    return () => {
      window.clearTimeout(scrollTimer);
      window.clearTimeout(clearTimer);
    };
  }, [coach]);

  if (dismissed || journey.isLoading || !coach) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

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
    <div
      ref={rootRef}
      className={`card border border-violet-300 bg-gradient-to-r from-violet-50/95 via-amber-50/70 to-fuchsia-50/60 dark:border-violet-800 dark:from-violet-950/50 dark:via-amber-950/30 dark:to-fuchsia-950/30 ${
        highlighted ? "ring-2 ring-violet-400 shadow-lg shadow-violet-200/50 dark:shadow-violet-900/30" : ""
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-violet-700 dark:text-violet-300">
            🎓 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{coach.celebrate}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-violet-100 px-2.5 py-1 text-xs font-medium text-violet-900 dark:bg-violet-950/50 dark:text-violet-100">
              {d.progress(coach.done_count, coach.total)}
            </span>
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-900 dark:bg-amber-950/50 dark:text-amber-100">
              {d.paperGraduated(coach.paper_graduated_count)}
            </span>
            <span className="rounded-full bg-fuchsia-100 px-2.5 py-1 text-xs font-medium text-fuchsia-900 dark:bg-fuchsia-950/50 dark:text-fuchsia-100">
              {d.followers(coach.followers)}
            </span>
            {coach.on_leaderboard && coach.leaderboard_rank != null && (
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100">
                {d.onBoard(coach.leaderboard_rank)}
              </span>
            )}
          </div>
          {coach.report_title && (
            <p className="mt-2 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.report_title}</p>
          )}
          <p className="mt-2 text-sm text-violet-900/90 dark:text-violet-100/90">{coach.message}</p>

          <div className="mt-4 rounded-lg border border-violet-300/50 bg-white/60 p-3 dark:border-violet-800 dark:bg-slate-900/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-violet-800 dark:text-violet-200">
              {coach.guide_title}
            </p>
            <ol className="mt-3 grid gap-2 sm:grid-cols-3">
              {coach.guide_steps.map((step) => {
                const stepCta =
                  step.cta_action in stages
                    ? stageToCtaLabel(step.cta_action, stages)
                    : d.stepGo;
                return (
                  <li
                    key={step.step}
                    className="rounded-lg border border-violet-200 bg-violet-50/80 px-2.5 py-2 dark:border-violet-900 dark:bg-violet-950/30"
                  >
                    <div className="flex items-start gap-2">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-violet-500 text-xs font-bold text-white">
                        {step.step}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-violet-950 dark:text-violet-50">
                          {step.label}
                        </p>
                        <p className="mt-1 text-[11px] leading-snug text-violet-900/80 dark:text-violet-100/80">
                          {step.hint}
                        </p>
                        <Link
                          to={step.cta_path}
                          className="mt-2 inline-block text-[10px] font-semibold text-brand-600 hover:underline dark:text-brand-400"
                        >
                          {stepCta}
                        </Link>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.feed_path} className="btn-primary whitespace-nowrap text-xs">
            {d.viewFeed}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={copyLink}>
            {d.copyLink}
          </button>
          <Link to={coach.cta_path} className="btn whitespace-nowrap text-xs">
            {ctaLabel}
          </Link>
          <Link to={coach.profile_path} className="btn whitespace-nowrap text-xs">
            {d.viewProfile}
          </Link>
          <HandbookExportButtons compact />
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

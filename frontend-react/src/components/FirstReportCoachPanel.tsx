import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_REPORT_WELCOME_KEY } from "../lib/onboardingFocus";
import { burstConfetti } from "../lib/confetti";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";
import HandbookExportButtons from "./HandbookExportButtons";

const DISMISS_KEY = "quantlab-first-report-dismissed";

type Props = {
  placement?: "dashboard" | "report";
  reportId?: string;
};

export default function FirstReportCoachPanel({ placement = "dashboard", reportId }: Props) {
  const d = useLocale((s) => s.dict.firstReportCoach);
  const stages = useLocale((s) => s.dict.stages);
  const [highlighted, setHighlighted] = useState(false);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const coach = journey.data?.first_report_coaching;
  const freshReportId =
    typeof window !== "undefined" ? sessionStorage.getItem(FIRST_REPORT_WELCOME_KEY) : null;
  const visible =
    !dismissed &&
    !journey.isLoading &&
    Boolean(coach) &&
    !(placement === "dashboard" && freshReportId);

  useEffect(() => {
    if (!visible || placement !== "report" || !reportId) return;
    if (sessionStorage.getItem(FIRST_REPORT_WELCOME_KEY) !== reportId) return;
    sessionStorage.removeItem(FIRST_REPORT_WELCOME_KEY);
    burstConfetti(2800);
    const highlightTimer = window.setTimeout(() => setHighlighted(true), 80);
    const clearTimer = window.setTimeout(() => setHighlighted(false), 3200);
    return () => {
      window.clearTimeout(highlightTimer);
      window.clearTimeout(clearTimer);
    };
  }, [visible, placement, reportId]);

  if (!visible || !coach) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div
      className={`card border border-amber-200 bg-gradient-to-r from-amber-50/90 to-orange-50/50 dark:border-amber-900 dark:from-amber-950/40 dark:to-orange-950/20 ${
        placement === "report" ? "mb-6" : "animate-[pulse_2s_ease-in-out_1]"
      } ${
        highlighted ? "ring-2 ring-amber-400 shadow-lg shadow-amber-200/50 dark:shadow-amber-900/30" : ""
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
            🎓 {placement === "report" ? d.reportPageBadge : coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          {coach.academy_completed && coach.academy_xp != null && coach.academy_title && (
            <p className="mt-2 rounded-lg border border-amber-300/60 bg-amber-100/50 px-2.5 py-1.5 text-xs font-medium text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
              {d.academyEarned(coach.academy_title, coach.academy_xp)}
            </p>
          )}
          {coach.challenge_milestone_done && (
            <p className="mt-2 rounded-lg border border-violet-300/60 bg-violet-100/50 px-2.5 py-1.5 text-xs font-medium text-violet-900 dark:border-violet-800 dark:bg-violet-950/40 dark:text-violet-100">
              {d.challengeMilestone}
            </p>
          )}
          <p className="mt-2 text-sm text-amber-900/90 dark:text-amber-100/90">{coach.message}</p>
          <p className="mt-2 text-xs text-amber-800/80 dark:text-amber-200/80">
            {d.unlocked(coach.unlock_features)}
          </p>

          {coach.guide_steps.length > 0 && coach.paper_guide_title && (
            <div className="mt-4 rounded-lg border border-amber-300/50 bg-white/60 p-3 dark:border-amber-800 dark:bg-slate-900/40">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-200">
                {coach.paper_guide_title}
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
                      className="rounded-lg border border-amber-200 bg-amber-50/80 px-2.5 py-2 dark:border-amber-900 dark:bg-amber-950/30"
                    >
                      <div className="flex items-start gap-2">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500 text-xs font-bold text-white">
                          {step.step}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-amber-950 dark:text-amber-50">
                            {step.label}
                          </p>
                          <p className="mt-1 text-[11px] leading-snug text-amber-900/80 dark:text-amber-100/80">
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
          )}
          {placement === "dashboard" && (
            <div className="mt-4 rounded-lg border border-amber-300/40 bg-white/50 p-2.5 dark:bg-slate-900/30">
              <p className="mb-2 text-[10px] font-semibold uppercase text-amber-800 dark:text-amber-200">
                {d.saveHandbook}
              </p>
              <HandbookExportButtons compact />
            </div>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs">
            {ctaLabel}
          </Link>
          <Link to="/leaderboards?kind=paper_mastery" className="btn whitespace-nowrap text-xs">
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

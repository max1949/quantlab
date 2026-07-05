import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

const DISMISS_KEY = "quantlab-research-revisit-coach-dismissed";

export default function ResearchRevisitCoachPanel() {
  const d = useLocale((s) => s.dict.researchRevisitCoach);
  const stages = useLocale((s) => s.dict.stages);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const coach = journey.data?.research_revisit_coaching;

  if (dismissed || journey.isLoading || !coach) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="card border border-amber-200 bg-gradient-to-r from-amber-50/90 to-orange-50/50 dark:border-amber-900 dark:from-amber-950/40 dark:to-orange-950/30">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-200">
            👋 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{coach.message}</p>
          <p className="mt-2 text-xs text-amber-900/80 dark:text-amber-100/80">
            {d.unlocked(coach.unlock_features)}
          </p>

          {coach.guide_steps.length > 0 && coach.guide_title && (
            <div className="mt-4 rounded-lg border border-amber-300/50 bg-white/60 p-3 dark:border-amber-800 dark:bg-slate-900/40">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-900 dark:text-amber-100">
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
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs" onClick={dismiss}>
            {ctaLabel}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

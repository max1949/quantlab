import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_PROJECT_WELCOME_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

type Props = {
  projectId: string;
  backtestDone: boolean;
  backtestPending: boolean;
  onRunBacktest: () => void;
};

function dismissKey(projectId: string) {
  return `quantlab-first-project-coach-${projectId}`;
}

export default function FirstProjectCoachPanel({
  projectId,
  backtestDone,
  backtestPending,
  onRunBacktest,
}: Props) {
  const d = useLocale((s) => s.dict.firstProjectCoach);
  const stages = useLocale((s) => s.dict.stages);
  const [highlighted, setHighlighted] = useState(false);
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(dismissKey(projectId)) === "1",
  );

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const coach = journey.data?.first_project_coaching;
  const matches =
    coach != null &&
    coach.active_project_id === projectId &&
    !backtestDone &&
    !dismissed;

  useEffect(() => {
    if (!matches) return;
    if (sessionStorage.getItem(FIRST_PROJECT_WELCOME_KEY) !== projectId) return;
    sessionStorage.removeItem(FIRST_PROJECT_WELCOME_KEY);
    const scrollTimer = window.setTimeout(() => {
      document.getElementById("project-step-backtest")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      setHighlighted(true);
    }, 120);
    const clearTimer = window.setTimeout(() => setHighlighted(false), 3200);
    return () => {
      window.clearTimeout(scrollTimer);
      window.clearTimeout(clearTimer);
    };
  }, [matches, projectId]);

  if (!matches || journey.isLoading) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(dismissKey(projectId), "1");
    setDismissed(true);
  };

  return (
    <div
      className={`mb-6 card border border-brand-200 bg-gradient-to-r from-brand-50/90 to-cyan-50/50 dark:border-brand-900 dark:from-brand-950/40 dark:to-cyan-950/30 ${
        highlighted ? "ring-2 ring-brand-400 shadow-lg shadow-brand-200/50 dark:shadow-brand-900/30" : ""
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-700 dark:text-brand-300">
            🚀 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          {coach.factor_name && (
            <p className="mt-2 rounded-lg border border-brand-200 bg-white/70 px-2.5 py-1.5 text-xs text-brand-900 dark:border-brand-800 dark:bg-slate-900/50 dark:text-brand-100">
              {d.factorReady(coach.factor_name)}
            </p>
          )}
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{coach.message}</p>
          <p className="mt-2 text-xs text-brand-800/80 dark:text-brand-200/80">
            {d.unlocked(coach.unlock_features)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            className="btn-primary whitespace-nowrap text-xs"
            disabled={backtestPending}
            onClick={() => {
              dismiss();
              onRunBacktest();
            }}
          >
            {backtestPending ? d.running : ctaLabel}
          </button>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

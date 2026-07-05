import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_BACKTEST_WELCOME_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

type Props = {
  projectId: string;
  backtestDone: boolean;
  validationDone: boolean;
  validationPending: boolean;
  onRunValidation: () => void;
};

function dismissKey(projectId: string) {
  return `quantlab-first-backtest-coach-${projectId}`;
}

export default function FirstBacktestCoachPanel({
  projectId,
  backtestDone,
  validationDone,
  validationPending,
  onRunValidation,
}: Props) {
  const d = useLocale((s) => s.dict.firstBacktestCoach);
  const stages = useLocale((s) => s.dict.stages);
  const [highlighted, setHighlighted] = useState(false);
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(dismissKey(projectId)) === "1",
  );

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const coach = journey.data?.first_backtest_coaching;
  const matches =
    coach != null &&
    coach.active_project_id === projectId &&
    backtestDone &&
    !validationDone &&
    !dismissed;

  useEffect(() => {
    if (!matches) return;
    if (sessionStorage.getItem(FIRST_BACKTEST_WELCOME_KEY) !== projectId) return;
    sessionStorage.removeItem(FIRST_BACKTEST_WELCOME_KEY);
    const scrollTimer = window.setTimeout(() => {
      document.getElementById("project-step-validation")?.scrollIntoView({
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
      className={`mb-6 card border border-amber-200 bg-gradient-to-r from-amber-50/90 to-orange-50/50 dark:border-amber-900 dark:from-amber-950/40 dark:to-orange-950/30 ${
        highlighted ? "ring-2 ring-amber-400 shadow-lg shadow-amber-200/50 dark:shadow-amber-900/30" : ""
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
            📊 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{coach.message}</p>
          <p className="mt-2 text-xs text-amber-800/80 dark:text-amber-200/80">
            {d.unlocked(coach.unlock_features)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            className="btn-primary whitespace-nowrap text-xs"
            disabled={validationPending}
            onClick={() => {
              dismiss();
              onRunValidation();
            }}
          >
            {validationPending ? d.running : ctaLabel}
          </button>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_PAPER_ORDER_WELCOME_KEY, FIRST_LEADERBOARD_PAPER_WELCOME_KEY } from "../lib/onboardingFocus";
import { burstConfetti } from "../lib/confetti";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

type Props = {
  projectId?: string;
  placement?: "dashboard" | "project";
};

function dismissKey(projectId: string) {
  return `quantlab-first-paper-order-coach-${projectId}`;
}

export default function FirstPaperOrderCoachPanel({
  projectId,
  placement = "project",
}: Props) {
  const d = useLocale((s) => s.dict.firstPaperOrderCoach);
  const stages = useLocale((s) => s.dict.stages);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const coach = journey.data?.first_paper_order_coaching;
  const effectiveProjectId = projectId ?? coach?.active_project_id ?? "";
  const [highlighted, setHighlighted] = useState(false);
  const [dismissed, setDismissed] = useState(
    () => effectiveProjectId && localStorage.getItem(dismissKey(effectiveProjectId)) === "1",
  );
  const freshPaperOrder =
    typeof window !== "undefined" ? sessionStorage.getItem(FIRST_PAPER_ORDER_WELCOME_KEY) : null;
  const matches =
    coach != null &&
    effectiveProjectId &&
    coach.active_project_id === effectiveProjectId &&
    !dismissed &&
    !(placement === "dashboard" && freshPaperOrder);

  useEffect(() => {
    if (!matches) return;
    if (sessionStorage.getItem(FIRST_PAPER_ORDER_WELCOME_KEY) !== effectiveProjectId) return;
    sessionStorage.removeItem(FIRST_PAPER_ORDER_WELCOME_KEY);
    burstConfetti(3000);
    const scrollTimer = window.setTimeout(() => {
      document.getElementById("paper-tracking")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      setHighlighted(true);
    }, 120);
    const clearTimer = window.setTimeout(() => setHighlighted(false), 3200);
    return () => {
      window.clearTimeout(clearTimer);
      window.clearTimeout(scrollTimer);
    };
  }, [matches, effectiveProjectId]);

  if (!matches || journey.isLoading) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    if (effectiveProjectId) {
      localStorage.setItem(dismissKey(effectiveProjectId), "1");
    }
    setDismissed(true);
  };

  return (
    <div
      className={`mb-6 card border border-violet-200 bg-gradient-to-r from-violet-50/90 to-fuchsia-50/50 dark:border-violet-900 dark:from-violet-950/40 dark:to-fuchsia-950/30 ${
        highlighted ? "ring-2 ring-violet-400 shadow-lg shadow-violet-200/50 dark:shadow-violet-900/30" : ""
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-violet-700 dark:text-violet-300">
            📈 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{coach.message}</p>
          <p className="mt-2 text-xs text-violet-800/80 dark:text-violet-200/80">
            {d.unlocked(coach.unlock_features)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            to={coach.cta_path}
            className="btn-primary whitespace-nowrap text-xs"
            onClick={() => {
              sessionStorage.setItem(FIRST_LEADERBOARD_PAPER_WELCOME_KEY, "1");
              dismiss();
            }}
          >
            {ctaLabel}
          </Link>
          {coach.tracking_path && (
            <a href={coach.tracking_path} className="btn whitespace-nowrap text-xs" onClick={dismiss}>
              {d.viewTracking}
            </a>
          )}
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

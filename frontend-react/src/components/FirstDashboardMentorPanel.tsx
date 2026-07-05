import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMentor, getResearchJourney } from "../api/endpoints";
import { FIRST_MENTOR_WELCOME_KEY } from "../lib/onboardingFocus";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

const DISMISS_KEY = "quantlab-first-mentor-welcome-dismissed";

export default function FirstDashboardMentorPanel() {
  const user = useAuth((s) => s.user);
  const d = useLocale((s) => s.dict.firstMentorWelcome);
  const dash = useLocale((s) => s.dict.dashboard);
  const stages = useLocale((s) => s.dict.stages);
  const [active, setActive] = useState(false);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");

  const mentor = useQuery({ queryKey: ["mentor"], queryFn: getMentor });
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  useEffect(() => {
    if (dismissed) return;
    if (sessionStorage.getItem(FIRST_MENTOR_WELCOME_KEY) === "1") {
      sessionStorage.removeItem(FIRST_MENTOR_WELCOME_KEY);
      setActive(true);
    }
  }, [dismissed]);

  if (!active || dismissed || mentor.isLoading || journey.isLoading) return null;

  const guide = journey.data?.quickstart_guide;
  const m = mentor.data;
  if (!guide || !m) return null;

  const current = guide.steps[guide.current_index];
  const stepCta =
    current && current.cta_action in stages
      ? stageToCtaLabel(current.cta_action, stages)
      : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
    setActive(false);
  };

  return (
    <div className="card border border-brand-200 bg-gradient-to-r from-brand-50/90 to-violet-50/50 dark:border-brand-900 dark:from-brand-950/40 dark:to-violet-950/30">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <span className="text-2xl">🤖</span>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-700 dark:text-brand-300">
              {d.badge}
            </p>
            <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">
              {dash.aiMentor} · {m.title}
            </p>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              {user && (
                <span className="font-medium text-slate-800 dark:text-slate-100">
                  {dash.welcome(user.username)}{" "}
                </span>
              )}
              {m.message}
            </p>
            {current && !current.done && (
              <p className="mt-2 rounded-lg border border-brand-200 bg-white/70 px-2.5 py-1.5 text-xs text-brand-900 dark:border-brand-800 dark:bg-slate-900/50 dark:text-brand-100">
                {d.firstStep(current.label)}
              </p>
            )}
            <p className="mt-2 text-[11px] text-slate-400">{m.disclaimer}</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {current && !current.done && (
            <Link to={current.cta_path} className="btn-primary whitespace-nowrap text-xs">
              {stepCta}
            </Link>
          )}
          <a href="#quickstart" className="btn whitespace-nowrap text-xs">
            {d.openQuickstart}
          </a>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.gotIt}
          </button>
        </div>
      </div>
    </div>
  );
}

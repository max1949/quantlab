import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMentor, getResearchJourney } from "../api/endpoints";
import { FIRST_MENTOR_WELCOME_KEY } from "../lib/onboardingFocus";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { stageToCtaLabel, stageToRoute } from "../lib/nav";

const DISMISS_KEY = "quantlab-first-mentor-welcome-dismissed";

type Props = {
  onVisibilityChange?: (visible: boolean) => void;
};

export default function FirstDashboardMentorPanel({ onVisibilityChange }: Props) {
  const user = useAuth((s) => s.user);
  const navigate = useNavigate();
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

  const visible =
    active && !dismissed && !mentor.isLoading && !journey.isLoading && Boolean(mentor.data);

  useEffect(() => {
    onVisibilityChange?.(visible);
  }, [visible, onVisibilityChange]);

  if (!visible) return null;

  const guide = journey.data?.quickstart_guide;
  const m = mentor.data!;

  const current = guide?.steps[guide.current_index];
  const templateStart = m.stage === "create_project" && Boolean(m.recommended_template);
  const primaryRoute = templateStart
    ? stageToRoute(m.stage, m.recommended_template, null, m.regime_pick?.symbol)
    : current?.cta_path;
  const primaryLabel = templateStart
    ? stageToCtaLabel(m.stage, stages)
    : current && current.cta_action in stages
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
            {m.regime_pick?.template_title && (
              <p className="mt-2 rounded-lg border border-violet-200 bg-violet-50/60 px-2.5 py-1.5 text-xs text-violet-900 dark:border-violet-900 dark:bg-violet-950/30 dark:text-violet-100">
                {dash.mentorRegime(
                  m.regime_pick.symbol,
                  m.regime_pick.regime_label ?? "",
                  m.regime_pick.template_title,
                  m.regime_pick.fit_verdict,
                  m.regime_pick.fit_score,
                )}
                {m.regime_pick.coach_hint && (
                  <span className="opacity-90"> — {m.regime_pick.coach_hint}</span>
                )}
              </p>
            )}
            {current && !current.done && !templateStart && (
              <p className="mt-2 rounded-lg border border-brand-200 bg-white/70 px-2.5 py-1.5 text-xs text-brand-900 dark:border-brand-800 dark:bg-slate-900/50 dark:text-brand-100">
                {d.firstStep(current.label)}
              </p>
            )}
            {templateStart && m.regime_pick?.template_title && (
              <p className="mt-2 rounded-lg border border-brand-200 bg-white/70 px-2.5 py-1.5 text-xs text-brand-900 dark:border-brand-800 dark:bg-slate-900/50 dark:text-brand-100">
                {d.templatePick(m.regime_pick.template_title)}
              </p>
            )}
            <p className="mt-2 text-[11px] text-slate-400">{m.disclaimer}</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {primaryRoute && (
            templateStart ? (
              <button
                type="button"
                className="btn-primary whitespace-nowrap text-xs"
                onClick={() => {
                  dismiss();
                  navigate(primaryRoute);
                }}
              >
                {primaryLabel}
              </button>
            ) : (
              <Link
                to={primaryRoute}
                className="btn-primary whitespace-nowrap text-xs"
                onClick={dismiss}
              >
                {primaryLabel}
              </Link>
            )
          )}
          {guide && (
            <a href="#quickstart" className="btn whitespace-nowrap text-xs">
              {d.openQuickstart}
            </a>
          )}
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.gotIt}
          </button>
        </div>
      </div>
    </div>
  );
}

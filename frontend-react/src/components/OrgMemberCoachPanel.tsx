import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_ORG_MEMBER_WELCOME_KEY } from "../lib/onboardingFocus";
import { burstConfetti } from "../lib/confetti";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

function dismissKey(orgId: string) {
  return `quantlab-org-member-coach-${orgId}`;
}

export default function OrgMemberCoachPanel() {
  const d = useLocale((s) => s.dict.orgMemberCoach);
  const stages = useLocale((s) => s.dict.stages);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const coach = journey.data?.org_member_coaching;
  const orgId = coach?.org_id ?? "";
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (orgId) {
      setDismissed(localStorage.getItem(dismissKey(orgId)) === "1");
    }
  }, [orgId]);
  const freshWelcome =
    typeof window !== "undefined" && orgId
      ? sessionStorage.getItem(FIRST_ORG_MEMBER_WELCOME_KEY) === orgId
      : false;
  const matches = coach != null && orgId && !dismissed;

  useEffect(() => {
    if (!matches || !freshWelcome) return;
    sessionStorage.removeItem(FIRST_ORG_MEMBER_WELCOME_KEY);
    burstConfetti(2800);
  }, [matches, freshWelcome]);

  if (!matches || journey.isLoading) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(dismissKey(orgId), "1");
    setDismissed(true);
  };

  return (
    <div className="card border border-indigo-200 bg-gradient-to-r from-indigo-50/90 to-brand-50/50 dark:border-indigo-900 dark:from-indigo-950/40 dark:to-brand-950/30">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700 dark:text-indigo-300">
            🏢 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{coach.message}</p>
          <p className="mt-2 text-xs text-indigo-800/80 dark:text-indigo-200/80">
            {d.unlocked(coach.unlock_features)}
          </p>

          {coach.guide_steps.length > 0 && coach.guide_title && (
            <div className="mt-4 rounded-lg border border-indigo-300/50 bg-white/60 p-3 dark:border-indigo-800 dark:bg-slate-900/40">
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
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
                      className="rounded-lg border border-indigo-200 bg-indigo-50/80 px-2.5 py-2 dark:border-indigo-900 dark:bg-indigo-950/30"
                    >
                      <div className="flex items-start gap-2">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-500 text-xs font-bold text-white">
                          {step.step}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-indigo-950 dark:text-indigo-50">
                            {step.label}
                          </p>
                          <p className="mt-1 text-[11px] leading-snug text-indigo-900/80 dark:text-indigo-100/80">
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
          <Link to={coach.org_path} className="btn whitespace-nowrap text-xs">
            {d.openOrg(coach.org_name)}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_ORG_PAGE_WELCOME_KEY } from "../lib/onboardingFocus";
import { burstConfetti } from "../lib/confetti";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

function dismissKey(orgId: string) {
  return `quantlab-org-page-coach-${orgId}`;
}

type Props = {
  orgId: string;
};

export default function OrgMemberPageCoachPanel({ orgId }: Props) {
  const d = useLocale((s) => s.dict.orgMemberPageCoach);
  const stages = useLocale((s) => s.dict.stages);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const coach = journey.data?.org_member_coaching;
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (orgId) {
      setDismissed(localStorage.getItem(dismissKey(orgId)) === "1");
    }
  }, [orgId]);

  const freshWelcome =
    typeof window !== "undefined"
      ? sessionStorage.getItem(FIRST_ORG_PAGE_WELCOME_KEY) === orgId
      : false;
  const matches = coach != null && coach.org_id === orgId && !dismissed;

  useEffect(() => {
    if (!matches || !freshWelcome) return;
    sessionStorage.removeItem(FIRST_ORG_PAGE_WELCOME_KEY);
    burstConfetti(2400);
    const scrollTimer = window.setTimeout(() => {
      document.getElementById("org-catalog")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 200);
    return () => window.clearTimeout(scrollTimer);
  }, [matches, freshWelcome]);

  if (!matches || journey.isLoading) return null;

  const ctaLabel =
    coach.cta_action in stages ? stageToCtaLabel(coach.cta_action, stages) : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(dismissKey(orgId), "1");
    setDismissed(true);
  };

  return (
    <div className="mb-6 rounded-xl border border-indigo-200 bg-gradient-to-r from-indigo-50/80 to-brand-50/50 p-4 dark:border-indigo-900 dark:from-indigo-950/40 dark:to-brand-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
        🏢 {coach.badge}
      </p>
      <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{d.pageHint}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to={coach.cta_path} className="btn-primary text-xs" onClick={dismiss}>
          {ctaLabel}
        </Link>
        <a href="#org-catalog" className="btn text-xs">
          {d.browseCatalog}
        </a>
        <Link to="/app" className="btn text-xs">
          {d.openWorkspace}
        </Link>
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

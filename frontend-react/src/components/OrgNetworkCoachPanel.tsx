import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_FEED_FOLLOW_WELCOME_KEY } from "../lib/onboardingFocus";
import { NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";
import { useLocale } from "../store/locale";

function dismissKey(orgId: string) {
  return `quantlab-org-network-coach-${orgId}`;
}

type Props = {
  /** When set, only show on matching org detail page */
  orgId?: string;
};

export default function OrgNetworkCoachPanel({ orgId: pageOrgId }: Props = {}) {
  const d = useLocale((s) => s.dict.orgNetworkCoach);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const coach = journey.data?.org_network_coaching;
  const orgId = coach?.org_id ?? "";
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (orgId) setDismissed(localStorage.getItem(dismissKey(orgId)) === "1");
  }, [orgId]);

  if (!coach || !orgId || dismissed || journey.isLoading) return null;
  if (pageOrgId && coach.org_id !== pageOrgId) return null;

  const dismiss = () => {
    localStorage.setItem(dismissKey(orgId), "1");
    setDismissed(true);
  };

  return (
    <div
      className={`card border border-indigo-200 bg-gradient-to-r from-indigo-50/90 to-violet-50/60 dark:border-indigo-900 dark:from-indigo-950/40 dark:to-violet-950/30${pageOrgId ? " mb-6" : ""}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
            🏢 {coach.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.celebrate}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{coach.message}</p>
          <p className="mt-2 text-xs font-medium text-indigo-900/80 dark:text-indigo-100/80">
            {d.progress(coach.following, NETWORK_FOLLOW_TARGET)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            to={coach.feed_path}
            className="btn-primary whitespace-nowrap text-xs"
            onClick={() => sessionStorage.setItem(FIRST_FEED_FOLLOW_WELCOME_KEY, "1")}
          >
            {d.browseFeed}
          </Link>
          <Link to={`/orgs/${orgId}`} className="btn whitespace-nowrap text-xs">
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

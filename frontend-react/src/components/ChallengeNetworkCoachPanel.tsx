import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_FEED_FOLLOW_WELCOME_KEY } from "../lib/onboardingFocus";
import { journeyFollowingCount, NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";

const DISMISS_KEY = "quantlab-challenge-network-coach-dismissed";

export default function ChallengeNetworkCoachPanel() {
  const user = useAuth((s) => s.user);
  const d = useLocale((s) => s.dict.challengeNetworkCoach);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");

  const journey = useQuery({
    queryKey: ["research-journey"],
    queryFn: () => getResearchJourney(),
    enabled: Boolean(user),
  });

  const enrolled = journey.data?.challenge_enrolled === true;
  const followingCount = journeyFollowingCount(journey.data);
  const matches =
    Boolean(user) && !dismissed && enrolled && followingCount < NETWORK_FOLLOW_TARGET;

  if (!matches || journey.isLoading) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="mb-4 card border border-violet-200 bg-gradient-to-r from-violet-50/90 to-indigo-50/60 dark:border-violet-900 dark:from-violet-950/40 dark:to-indigo-950/30">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-violet-800 dark:text-violet-200">
            🏁 {d.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{d.title}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
          <p className="mt-2 text-xs font-medium text-violet-900/80 dark:text-violet-100/80">
            {d.progress(followingCount, NETWORK_FOLLOW_TARGET)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            to="/feed?focus=follow"
            className="btn-primary whitespace-nowrap text-xs"
            onClick={() => sessionStorage.setItem(FIRST_FEED_FOLLOW_WELCOME_KEY, "1")}
          >
            {d.browseFeed}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

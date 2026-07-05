import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_FEED_FOLLOW_WELCOME_KEY } from "../lib/onboardingFocus";
import { burstConfetti } from "../lib/confetti";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";

const DISMISS_KEY = "quantlab-feed-follow-coach-dismissed";

type Props = {
  onDiscoverMasters?: () => void;
};

export default function FeedFollowCoachPanel({ onDiscoverMasters }: Props) {
  const user = useAuth((s) => s.user);
  const d = useLocale((s) => s.dict.feedFollowCoach);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");

  const journey = useQuery({
    queryKey: ["research-journey"],
    queryFn: () => getResearchJourney(),
    enabled: Boolean(user),
  });

  const share = journey.data?.share_growth_coaching;
  const grad = journey.data?.mastery_graduation_coaching;
  const following = share?.following ?? grad?.followers ?? null;
  const freshWelcome =
    typeof window !== "undefined" && sessionStorage.getItem(FIRST_FEED_FOLLOW_WELCOME_KEY) === "1";

  const matches =
    Boolean(user) &&
    !dismissed &&
    (following ?? 0) === 0 &&
    (share != null || grad != null || freshWelcome);

  useEffect(() => {
    if (!matches || !freshWelcome) return;
    sessionStorage.removeItem(FIRST_FEED_FOLLOW_WELCOME_KEY);
    burstConfetti(2400);
  }, [matches, freshWelcome]);

  if (!matches || journey.isLoading) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="mb-4 card border border-sky-200 bg-gradient-to-r from-sky-50/90 to-indigo-50/50 dark:border-sky-900 dark:from-sky-950/40 dark:to-indigo-950/30">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-sky-800 dark:text-sky-200">
            🌱 {d.badge}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{d.title}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            className="btn-primary whitespace-nowrap text-xs"
            onClick={() => onDiscoverMasters?.()}
          >
            {d.browseFeed}
          </button>
          <Link to="/me/following" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.openFollowing}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

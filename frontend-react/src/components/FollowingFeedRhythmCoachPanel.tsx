import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { FIRST_FOLLOWING_FEED_WELCOME_KEY } from "../lib/onboardingFocus";
import { NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";
import { currentIsoWeek } from "../lib/isoWeek";
import { useLocale } from "../store/locale";

const DISMISS_KEY = "quantlab-following-rhythm-coach-dismissed";
const WEEK_KEY = "quantlab-following-rhythm-week";

type Props = {
  hasReports: boolean;
  highlightActive: boolean;
  replicationReturnActive?: boolean;
};

export default function FollowingFeedRhythmCoachPanel({
  hasReports,
  highlightActive,
  replicationReturnActive = false,
}: Props) {
  const d = useLocale((s) => s.dict.followingFeedRhythm);
  const [dismissedForever, setDismissedForever] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");
  const [weekDismissed, setWeekDismissed] = useState(
    () => typeof window !== "undefined" && localStorage.getItem(WEEK_KEY) === currentIsoWeek(),
  );

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const following = journey.data?.social_following_count ?? 0;
  const freshMilestone =
    typeof window !== "undefined" && sessionStorage.getItem(FIRST_FOLLOWING_FEED_WELCOME_KEY) === "1";

  const matches =
    !dismissedForever &&
    !weekDismissed &&
    !highlightActive &&
    !freshMilestone &&
    !replicationReturnActive &&
    following >= NETWORK_FOLLOW_TARGET &&
    hasReports &&
    !journey.isLoading;

  if (!matches) return null;

  const dismissWeek = () => {
    localStorage.setItem(WEEK_KEY, currentIsoWeek());
    setWeekDismissed(true);
  };

  const dismissForever = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissedForever(true);
  };

  return (
    <div className="mb-4 card border border-sky-200 bg-gradient-to-r from-sky-50/90 to-cyan-50/60 dark:border-sky-900 dark:from-sky-950/40 dark:to-cyan-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-sky-800 dark:text-sky-200">
        📅 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <p className="mt-2 text-xs text-sky-900/80 dark:text-sky-100/80">{d.hint}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <a href="#following-feed-grid" className="btn-primary text-xs">
          {d.pickReport}
        </a>
        <button type="button" className="btn text-xs" onClick={dismissWeek}>
          {d.dismiss}
        </button>
        <button type="button" className="btn-ghost text-xs" onClick={dismissForever}>
          {d.dismissForever}
        </button>
      </div>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { currentIsoWeek } from "../lib/isoWeek";
import { NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";
import { useLocale } from "../store/locale";

const WEEK_KEY = "quantlab-project-replication-rhythm-week";

type Props = {
  projectId: string;
  replicationActive: boolean;
};

export default function ProjectReplicationRhythmPanel({ projectId: _projectId, replicationActive }: Props) {
  const d = useLocale((s) => s.dict.projectReplicationRhythm);
  const [weekDismissed, setWeekDismissed] = useState(
    () => typeof window !== "undefined" && localStorage.getItem(WEEK_KEY) === currentIsoWeek(),
  );
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const following = journey.data?.social_following_count ?? 0;
  const networkReady = following >= NETWORK_FOLLOW_TARGET;

  const matches = !weekDismissed && networkReady && !replicationActive && !journey.isLoading;

  if (!matches) return null;

  const dismiss = () => {
    localStorage.setItem(WEEK_KEY, currentIsoWeek());
    setWeekDismissed(true);
  };

  return (
    <div className="mb-4 card border border-violet-200 bg-gradient-to-r from-violet-50/80 to-indigo-50/50 dark:border-violet-900 dark:from-violet-950/40 dark:to-indigo-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-violet-800 dark:text-violet-200">
        🔁 {d.badge}
      </p>
      <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <p className="mt-2 text-xs text-violet-900/80 dark:text-violet-100/80">{d.hint}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to="/me/following" className="btn-primary text-xs">
          {d.openFollowing}
        </Link>
        <Link to="/feed" className="btn text-xs">
          {d.browseFeed}
        </Link>
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

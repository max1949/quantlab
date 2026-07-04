import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { stageToCtaLabel } from "../lib/nav";

export default function ChallengePaperCoachPanel() {
  const d = useLocale((s) => s.dict.challengePaperCoach);
  const stages = useLocale((s) => s.dict.stages);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: getResearchJourney });

  const coach = journey.data?.challenge_paper_coaching;
  if (!coach) return null;

  const ctaLabel =
    coach.cta_action in stages
      ? stageToCtaLabel(coach.cta_action, stages)
      : d.ctaDefault;

  return (
    <div className="card border border-amber-200 bg-gradient-to-r from-amber-50/80 to-orange-50/50 dark:border-amber-900 dark:from-amber-950/30 dark:to-orange-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
            {d.badge(coach.next_day, coach.next_title)}
          </p>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{coach.message}</p>
          {coach.attention_linked && (
            <p className="mt-2 text-xs text-amber-800/90 dark:text-amber-200/90">{d.linkedHint}</p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs">
            {ctaLabel}
          </Link>
          <Link to="/challenges" className="btn whitespace-nowrap text-xs">
            {d.viewChallenge}
          </Link>
        </div>
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { Spinner } from "./ui";

export default function MasteryGoalPanel() {
  const d = useLocale((s) => s.dict.masteryGoal);
  const stages = useLocale((s) => s.dict.masteryPath.stages);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: getResearchJourney });

  if (journey.isLoading) return <Spinner />;
  if (!journey.data?.mastery_goal) return null;

  const g = journey.data.mastery_goal;
  const activeId = journey.data.active_project_id;
  const nextStage = g.mastery_next_action
    ? stages[g.mastery_next_action as keyof typeof stages] ?? g.mastery_next_action
    : null;

  return (
    <div className="card border border-emerald-100 bg-gradient-to-r from-emerald-50/80 to-brand-50/40 dark:border-emerald-900 dark:from-emerald-950/30 dark:to-brand-950/20">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{d.title}</h3>
          <p className="text-xs text-slate-500">{d.subtitle}</p>
        </div>
        {g.on_leaderboard && g.leaderboard_rank != null ? (
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 dark:bg-emerald-900 dark:text-emerald-100">
            {d.onBoard(g.leaderboard_rank)}
          </span>
        ) : (
          <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-slate-900 dark:text-slate-300">
            {d.graduatedCount(g.paper_graduated_count, g.paper_tracking_count)}
          </span>
        )}
      </div>

      <p className="mb-3 text-sm text-slate-700 dark:text-slate-200">{g.hint}</p>

      {g.mastery_progress_pct > 0 && !g.on_leaderboard && (
        <div className="mb-3">
          <div className="mb-1 flex justify-between text-xs text-slate-500">
            <span>{d.masteryPath}</span>
            <span>{g.mastery_progress_pct}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all"
              style={{ width: `${g.mastery_progress_pct}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {g.on_leaderboard ? (
          <Link to="/leaderboards?kind=paper_mastery" className="btn-primary text-xs">
            {d.viewBoard}
          </Link>
        ) : g.paper_ready && activeId ? (
          <Link to={`/projects/${activeId}`} className="btn-primary text-xs">
            {d.paperCta}
          </Link>
        ) : activeId && nextStage ? (
          <Link to={`/projects/${activeId}`} className="btn-primary text-xs">
            {d.goProject(nextStage)}
          </Link>
        ) : (
          <Link to="/templates" className="btn-primary text-xs">
            {d.fromTemplate}
          </Link>
        )}
        <Link to="/leaderboards?kind=paper_mastery" className="btn text-xs">
          {d.viewBoard}
        </Link>
      </div>
    </div>
  );
}

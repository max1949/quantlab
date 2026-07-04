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

      {!g.on_leaderboard && g.graduated_needed != null && g.graduated_needed > 0 && (
        <div className="mb-3 rounded-lg border border-sky-200 bg-sky-50/70 px-3 py-2 text-xs text-sky-900 dark:border-sky-900 dark:bg-sky-950/30 dark:text-sky-100">
          <p className="font-medium">
            {d.gapToBoard(g.graduated_needed, g.cutoff_graduated ?? 0, g.board_limit)}
          </p>
          {g.leaderboard_rank != null && g.ranks_outside_board != null && g.ranks_outside_board > 0 && (
            <p className="mt-1 opacity-90">
              {d.rankOutside(g.leaderboard_rank, g.ranks_outside_board, g.board_limit)}
            </p>
          )}
        </div>
      )}

      {!g.on_leaderboard && g.needs_tracking_boost && (
        <div className="mb-3 rounded-lg border border-violet-200 bg-violet-50/70 px-3 py-2 text-xs text-violet-900 dark:border-violet-900 dark:bg-violet-950/30 dark:text-violet-100">
          <p className="font-medium">{d.trackingBoost}</p>
        </div>
      )}

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

      {g.challenge_paper_milestones?.some((m) => !m.completed) && (
        <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50/60 px-3 py-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
          <p className="font-medium">{d.challengePaperTitle}</p>
          {g.challenge_paper_milestones
            .filter((m) => !m.completed)
            .map((m) => (
              <p key={m.code} className="mt-1">
                🏅 {d.challengePaperItem(m.title, m.mastery_stage_label ?? m.mastery_stage ?? "")}
              </p>
            ))}
          <Link to="/challenges" className="mt-2 inline-block font-medium text-brand-600 hover:underline">
            {d.challengePaperCta}
          </Link>
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

import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getLeaderboard, getPaperMasteryMeta, getResearchJourney } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import type { LeaderboardKind } from "../api/types";

const medals = ["🥇", "🥈", "🥉"];
const VALID_KINDS: LeaderboardKind[] = [
  "researcher",
  "contributor",
  "newcomer",
  "improved",
  "paper_mastery",
];

function parseKind(raw: string | null): LeaderboardKind {
  if (raw && VALID_KINDS.includes(raw as LeaderboardKind)) {
    return raw as LeaderboardKind;
  }
  return "researcher";
}

export default function Leaderboards() {
  const l = useLocale((s) => s.dict.leaderboards);
  const user = useAuth((s) => s.user);
  const [params, setParams] = useSearchParams();
  const kind = parseKind(params.get("kind"));

  const setKind = (next: LeaderboardKind) => {
    setParams(next === "researcher" ? {} : { kind: next }, { replace: true });
  };

  const tabs: { kind: LeaderboardKind; label: string }[] = [
    { kind: "researcher", label: l.researcher },
    { kind: "contributor", label: l.contributor },
    { kind: "newcomer", label: l.newcomer },
    { kind: "improved", label: l.improved },
    { kind: "paper_mastery", label: l.paperMastery },
  ];

  const q = useQuery({
    queryKey: ["leaderboard", kind],
    queryFn: () => getLeaderboard(kind),
  });

  const paperMeta = useQuery({
    queryKey: ["paper-mastery-meta"],
    queryFn: getPaperMasteryMeta,
    enabled: kind === "paper_mastery",
  });

  const journey = useQuery({
    queryKey: ["research-journey"],
    queryFn: getResearchJourney,
    enabled: Boolean(user) && kind === "paper_mastery",
  });

  const masteryGoal = journey.data?.mastery_goal;
  const onBoard = masteryGoal?.on_leaderboard ?? false;
  const myRank = masteryGoal?.leaderboard_rank ?? null;
  const cutoff = paperMeta.data?.cutoff;
  const cutoffRank = cutoff?.rank ?? null;

  const myGraduated = masteryGoal?.paper_graduated_count ?? 0;
  const cutoffGraduated = cutoff?.graduated ?? 1;
  const barPct =
    cutoffGraduated > 0 ? Math.min(100, Math.round((myGraduated / cutoffGraduated) * 100)) : 0;

  return (
    <div>
      <PageTitle title={l.title} subtitle={l.subtitle} />

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.kind}
            onClick={() => setKind(t.kind)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              kind === t.kind
                ? "bg-brand-600 text-white"
                : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {kind === "paper_mastery" && (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50/60 px-4 py-3 text-sm dark:border-emerald-900 dark:bg-emerald-950/30">
          <p className="font-medium text-emerald-900 dark:text-emerald-100">{l.paperMasteryTitle}</p>
          <p className="mt-1 text-emerald-800/90 dark:text-emerald-200/90">{l.paperMasteryHow}</p>
          {user && masteryGoal && (
            <p className="mt-2 text-emerald-900 dark:text-emerald-100">
              {onBoard && myRank != null
                ? l.yourRankOnBoard(myRank, masteryGoal.paper_graduated_count)
                : masteryGoal.graduated_needed != null && masteryGoal.graduated_needed > 0
                  ? l.gapToBoardLine(
                      masteryGoal.graduated_needed,
                      masteryGoal.cutoff_graduated ?? 0,
                      masteryGoal.board_limit,
                    )
                  : masteryGoal.needs_tracking_boost
                    ? l.trackingBoostLine(masteryGoal.paper_graduated_count)
                    : l.notOnBoardYet(masteryGoal.paper_graduated_count)}
            </p>
          )}
          {user && !onBoard && (
            <Link to="/dashboard" className="mt-2 inline-block text-xs font-medium text-brand-600 hover:underline">
              {l.goDashboard}
            </Link>
          )}
        </div>
      )}

      {kind === "paper_mastery" && cutoff && (
        <div className="mb-4 card border border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-amber-950 dark:text-amber-100">
                {l.cutoffTitle(cutoff.rank, cutoff.graduated, cutoff.tracking, paperMeta.data?.board_limit ?? 50)}
              </p>
              {cutoff.username && (
                <p className="mt-1 text-xs text-amber-800/90 dark:text-amber-200/90">
                  {l.cutoffHolder(cutoff.username)}
                </p>
              )}
              {paperMeta.data && (
                <p className="mt-1 text-xs text-slate-500">
                  {l.totalRanked(paperMeta.data.total_ranked, paperMeta.data.board_full)}
                </p>
              )}
            </div>
            <span className="rounded-full bg-amber-200/80 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-amber-900 dark:bg-amber-900 dark:text-amber-100">
              {l.cutoffBadge}
            </span>
          </div>
          {user && masteryGoal && !onBoard && cutoffGraduated > 0 && (
            <div className="mt-3">
              <div className="mb-1 flex justify-between text-xs text-slate-600 dark:text-slate-300">
                <span>{l.youProgress(myGraduated)}</span>
                <span>{l.cutoffProgress(cutoffGraduated)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className="h-full rounded-full bg-amber-500 transition-all"
                  style={{ width: `${barPct}%` }}
                />
              </div>
              {barPct >= 100 && masteryGoal.needs_tracking_boost && (
                <p className="mt-1 text-xs text-violet-700 dark:text-violet-300">{l.trackingBoostLine(myGraduated)}</p>
              )}
            </div>
          )}
        </div>
      )}

      {q.isLoading ? (
        <Spinner />
      ) : q.isError ? (
        <ErrorBox message={apiErrorMessage(q.error)} />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">{l.rank}</th>
                <th className="px-4 py-3">{l.user}</th>
                <th className="px-4 py-3">Lv</th>
                <th className="px-4 py-3 text-right">
                  {q.data?.[0]?.metric_label ?? l.score}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {q.data?.map((row) => {
                const isMe = user?.id === row.user_id;
                const isCutoff =
                  kind === "paper_mastery" &&
                  cutoffRank != null &&
                  row.rank === cutoffRank &&
                  (paperMeta.data?.board_full ?? false);
                return (
                  <tr
                    key={row.user_id}
                    id={isMe ? `lb-row-${row.user_id}` : undefined}
                    className={
                      isMe
                        ? "bg-emerald-50/80 ring-1 ring-inset ring-emerald-200 dark:bg-emerald-950/30 dark:ring-emerald-900"
                        : isCutoff
                          ? "bg-amber-50/60 dark:bg-amber-950/20"
                          : "hover:bg-slate-50"
                    }
                  >
                    <td className="px-4 py-3 font-semibold">
                      {medals[row.rank - 1] ?? row.rank}
                      {isMe && (
                        <span className="ml-1 text-[10px] font-normal text-emerald-700 dark:text-emerald-300">
                          {l.you}
                        </span>
                      )}
                      {isCutoff && (
                        <span className="ml-1 rounded bg-amber-200 px-1 py-0.5 text-[10px] font-medium text-amber-900 dark:bg-amber-900 dark:text-amber-100">
                          {l.cutoffBadge}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/u/${row.user_id}`}
                        className="font-medium text-brand-600 hover:underline"
                      >
                        {row.username}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-500">L{row.level}</td>
                    <td className="px-4 py-3 text-right font-semibold text-slate-800">
                      {typeof row.metric_value === "number"
                        ? Number(row.metric_value).toFixed(1)
                        : row.metric_value}
                    </td>
                  </tr>
                );
              })}
              {q.data && q.data.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                    {kind === "paper_mastery" ? l.paperMasteryEmpty : l.empty}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

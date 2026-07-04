import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getLeaderboard, getResearchJourney } from "../api/endpoints";
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

  const journey = useQuery({
    queryKey: ["research-journey"],
    queryFn: getResearchJourney,
    enabled: Boolean(user) && kind === "paper_mastery",
  });

  const masteryGoal = journey.data?.mastery_goal;
  const onBoard = masteryGoal?.on_leaderboard ?? false;
  const myRank = masteryGoal?.leaderboard_rank ?? null;

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
                return (
                  <tr
                    key={row.user_id}
                    id={isMe ? `lb-row-${row.user_id}` : undefined}
                    className={
                      isMe
                        ? "bg-emerald-50/80 ring-1 ring-inset ring-emerald-200 dark:bg-emerald-950/30 dark:ring-emerald-900"
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

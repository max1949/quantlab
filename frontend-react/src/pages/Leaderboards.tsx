import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getLeaderboard } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import type { LeaderboardKind } from "../api/types";

const tabs: { kind: LeaderboardKind; label: string }[] = [
  { kind: "researcher", label: "研究之星" },
  { kind: "contributor", label: "贡献之星" },
  { kind: "newcomer", label: "新秀榜" },
  { kind: "improved", label: "进步榜" },
];

const medals = ["🥇", "🥈", "🥉"];

export default function Leaderboards() {
  const [kind, setKind] = useState<LeaderboardKind>("researcher");
  const q = useQuery({
    queryKey: ["leaderboard", kind],
    queryFn: () => getLeaderboard(kind),
  });

  return (
    <div>
      <PageTitle title="研究员榜单" subtitle="多维度衡量研究贡献与成长" />

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

      {q.isLoading ? (
        <Spinner />
      ) : q.isError ? (
        <ErrorBox message={apiErrorMessage(q.error)} />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">名次</th>
                <th className="px-4 py-3">研究员</th>
                <th className="px-4 py-3">等级</th>
                <th className="px-4 py-3 text-right">
                  {q.data?.[0]?.metric_label ?? "分数"}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {q.data?.map((row) => (
                <tr key={row.user_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-semibold">
                    {medals[row.rank - 1] ?? row.rank}
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
              ))}
              {q.data && q.data.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                    暂无数据
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

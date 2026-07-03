import { useQuery } from "@tanstack/react-query";
import { getFactorCatalog } from "../api/endpoints";
import { useLocale } from "../store/locale";

type Props = {
  projectId: string;
  symbol?: string;
  timeframe: string;
  enabled?: boolean;
};

export default function FactorCatalogPanel({
  projectId,
  symbol,
  timeframe,
  enabled = true,
}: Props) {
  const t = useLocale((s) => s.dict.projectDetail);
  const q = useQuery({
    queryKey: ["factor-catalog", projectId, symbol, timeframe],
    queryFn: () => getFactorCatalog({ projectId, symbol, timeframe }),
    enabled: enabled && Boolean(projectId),
    staleTime: 60_000,
  });

  if (!enabled) return null;
  if (q.isLoading) {
    return <p className="mb-4 text-xs text-slate-400">{t.catalogLoading}</p>;
  }
  if (q.isError || !q.data || q.data.factors.length === 0) return null;

  const { factors, redundancy_pairs: pairs, high_overlap_count: overlap } = q.data;

  return (
    <div className="mb-6 card">
      <p className="font-semibold text-slate-800 dark:text-slate-100">{t.catalogTitle}</p>
      <p className="mt-1 text-xs text-slate-500">{t.catalogSubtitle(factors.length, overlap)}</p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-700">
              <th className="py-1 pr-2">{t.catalogColName}</th>
              <th className="py-1 pr-2">{t.catalogColKind}</th>
              <th className="py-1 pr-2">{t.catalogColSharpe}</th>
              <th className="py-1">{t.catalogColOos}</th>
            </tr>
          </thead>
          <tbody>
            {factors.map((f) => (
              <tr key={f.factor_id} className="border-b border-slate-100 dark:border-slate-800">
                <td className="py-1.5 pr-2 font-medium">{f.name}</td>
                <td className="py-1.5 pr-2 text-slate-500">{f.kind}</td>
                <td className="py-1.5 pr-2">{fmt(f.sharpe)}</td>
                <td className="py-1.5">{fmt(f.oos_sharpe)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pairs.length > 0 && (
        <div className="mt-3 text-xs text-slate-600 dark:text-slate-300">
          <p className="font-medium">{t.catalogOverlap}</p>
          <ul className="mt-1 list-inside list-disc">
            {pairs.slice(0, 3).map((p) => (
              <li key={`${p.factor_a}-${p.factor_b}`}>
                {t.catalogPair(p.name_a, p.name_b, p.r_squared)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function fmt(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return v.toFixed(2);
}

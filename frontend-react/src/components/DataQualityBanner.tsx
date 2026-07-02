import { useQuery } from "@tanstack/react-query";
import { getDataQuality } from "../api/endpoints";
import { useLocale } from "../store/locale";

type Props = {
  symbol: string;
  timeframe: string;
  enabled?: boolean;
};

export default function DataQualityBanner({ symbol, timeframe, enabled = true }: Props) {
  const t = useLocale((s) => s.dict.projectDetail);
  const q = useQuery({
    queryKey: ["data-quality", symbol, timeframe],
    queryFn: () => getDataQuality(symbol, timeframe),
    enabled: enabled && Boolean(symbol && timeframe),
    staleTime: 60_000,
  });

  if (!enabled || !symbol) return null;
  if (q.isLoading) {
    return (
      <p className="mb-4 text-xs text-slate-400">{t.dataQualityChecking}</p>
    );
  }
  if (q.isError || !q.data) return null;

  const d = q.data;
  if (d.passed) {
    return (
      <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50/60 px-3 py-2 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100">
        {t.dataQualityPass(d.grade)}
      </div>
    );
  }

  return (
    <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50/70 px-3 py-2 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
      <p className="font-medium">{t.dataQualityWarn(d.grade)}</p>
      <ul className="mt-1 list-inside list-disc text-xs opacity-90">
        {d.warnings.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { getVolRegime } from "../api/endpoints";
import { useLocale } from "../store/locale";

type Props = {
  symbol: string;
  timeframe: string;
  enabled?: boolean;
};

const regimeTone: Record<string, string> = {
  low: "border-sky-200 bg-sky-50/60 text-sky-900 dark:border-sky-900 dark:bg-sky-950/30 dark:text-sky-100",
  mid: "border-slate-200 bg-slate-50/60 text-slate-800 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-100",
  high: "border-rose-200 bg-rose-50/60 text-rose-900 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-100",
};

export default function VolRegimeBanner({ symbol, timeframe, enabled = true }: Props) {
  const t = useLocale((s) => s.dict.projectDetail);
  const q = useQuery({
    queryKey: ["vol-regime", symbol, timeframe],
    queryFn: () => getVolRegime(symbol, timeframe),
    enabled: enabled && Boolean(symbol && timeframe),
    staleTime: 120_000,
  });

  if (!enabled || !symbol) return null;
  if (q.isLoading) {
    return <p className="mb-4 text-xs text-slate-400">{t.regimeChecking}</p>;
  }
  if (q.isError || !q.data) return null;

  const d = q.data;
  const tone = regimeTone[d.regime] ?? regimeTone.mid;

  return (
    <div className={`mb-4 rounded-lg border px-3 py-2 text-sm ${tone}`}>
      <p className="font-medium">
        {t.regimeTitle(d.label, d.volatility_ann, Math.round(d.percentile * 100))}
      </p>
      <p className="mt-1 text-xs opacity-90">{d.hint}</p>
    </div>
  );
}

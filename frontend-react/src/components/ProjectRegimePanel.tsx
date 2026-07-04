import { Link } from "react-router-dom";
import { useLocale } from "../store/locale";
import type { ProjectQuality } from "../api/endpoints";
import type { VolRegime } from "../api/types";

type Props = {
  quality: ProjectQuality;
};

export default function ProjectRegimePanel({ quality }: Props) {
  const r = useLocale((s) => s.dict.projectRegime);
  const regime = quality.regime as VolRegime | null | undefined;
  if (!regime?.regime) return null;

  const symbol = quality.symbol ?? regime.symbol ?? "RB";
  const fitScore = regime.fit_score != null ? Number(regime.fit_score) : null;
  const lowFit = fitScore != null && fitScore < 55;
  const barPct = fitScore != null ? Math.min(100, Math.max(0, fitScore)) : 0;

  return (
    <div className="mb-6 card border border-violet-200 bg-violet-50/40 dark:border-violet-900 dark:bg-violet-950/25">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-violet-950 dark:text-violet-100">
            {r.title(symbol)}
          </h3>
          <p className="text-sm text-violet-800/90 dark:text-violet-200/90">
            {regime.regime_label ?? regime.label} · {r.asOf(regime.as_of)}
          </p>
        </div>
        {regime.fit_verdict && (
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              lowFit
                ? "bg-amber-200 text-amber-900 dark:bg-amber-900 dark:text-amber-100"
                : "bg-emerald-200 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100"
            }`}
          >
            {regime.fit_verdict}
            {fitScore != null ? ` · ${fitScore}` : ""}
          </span>
        )}
      </div>

      {regime.strategy_label && (
        <p className="text-sm text-slate-700 dark:text-slate-200">
          {r.strategy(regime.strategy_label)}
        </p>
      )}

      {fitScore != null && (
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-xs text-slate-500">
            <span>{r.fitLabel}</span>
            <span>{fitScore}/100</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
            <div
              className={`h-full rounded-full transition-all ${
                lowFit ? "bg-amber-500" : "bg-emerald-500"
              }`}
              style={{ width: `${barPct}%` }}
            />
          </div>
        </div>
      )}

      {regime.hint && (
        <p className="mt-3 text-xs text-slate-600 dark:text-slate-300">{regime.hint}</p>
      )}
      {regime.fit_hint && (
        <p className="mt-1 text-xs text-violet-800 dark:text-violet-200">{regime.fit_hint}</p>
      )}

      {lowFit && (
        <Link
          to={`/templates?symbol=${encodeURIComponent(symbol)}`}
          className="mt-3 inline-block text-sm font-medium text-brand-600 hover:underline"
        >
          {r.tryOtherTemplate}
        </Link>
      )}
    </div>
  );
}

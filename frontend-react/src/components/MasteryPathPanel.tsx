import { useLocale } from "../store/locale";
import type { ProjectQuality } from "../api/endpoints";

type Props = {
  quality: ProjectQuality;
  onAction: (action: string) => void;
};

const STAGE_KEYS = ["start", "backtest", "validate", "graduate", "paper", "track", "share"] as const;

export default function MasteryPathPanel({ quality, onAction }: Props) {
  const m = useLocale((s) => s.dict.masteryPath);
  const mastery = quality.mastery;
  if (!mastery) return null;

  const currentIdx = mastery.stage_index ?? 0;

  return (
    <div className="mb-6 card border border-brand-100 bg-brand-50/30 dark:border-brand-900 dark:bg-brand-950/20">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{m.title}</h3>
          <p className="text-xs text-slate-500">{m.subtitle}</p>
        </div>
        <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900 dark:text-brand-200">
          {m.progress(mastery.progress_pct ?? 0)}
        </span>
      </div>

      <ol className="mb-4 grid gap-2 sm:grid-cols-7">
        {STAGE_KEYS.map((key, idx) => {
          const done = idx < currentIdx || (key === "share" && quality.mastery?.stage === "share");
          const active = idx === currentIdx;
          return (
            <li
              key={key}
              className={`rounded-lg border px-2 py-2 text-center text-xs ${
                done
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
                  : active
                    ? "border-brand-400 bg-white font-semibold text-brand-800 ring-2 ring-brand-300 dark:bg-slate-900 dark:text-brand-200"
                    : "border-slate-200 bg-white/50 text-slate-400 dark:border-slate-700 dark:bg-slate-900/30"
              }`}
            >
              {done && "✓ "}
              {m.stages[key]}
            </li>
          );
        })}
      </ol>

      {quality.regime && (
        <p className="mb-3 text-xs text-slate-600 dark:text-slate-300">
          {m.regimeHint(
            String(quality.regime.regime ?? "—"),
            quality.regime.fit_score != null ? Number(quality.regime.fit_score) : null,
            quality.regime.fit_verdict ? String(quality.regime.fit_verdict) : null,
          )}
        </p>
      )}

      {quality.paper_ready && mastery.stage === "track" ? (
        <div className="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm text-brand-900 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-100">
          <p className="font-medium">{m.trackReady}</p>
          <button type="button" className="btn mt-2 text-xs" onClick={() => onAction("track")}>
            {m.trackCta}
          </button>
        </div>
      ) : quality.paper_ready ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
          <p className="font-medium">{m.paperReady}</p>
          <button type="button" className="btn-primary mt-2 text-xs" onClick={() => onAction("paper")}>
            {m.paperCta}
          </button>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white/70 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900/40">
          <p className="font-medium text-slate-700 dark:text-slate-200">{m.nextLabel(m.stages[mastery.next_action as keyof typeof m.stages] ?? mastery.next_action)}</p>
          {quality.paper_reasons && quality.paper_reasons.length > 0 && (
            <ul className="mt-1 list-inside list-disc text-xs text-slate-500">
              {quality.paper_reasons.slice(0, 3).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="btn mt-2 text-xs"
            onClick={() => onAction(mastery.next_action)}
          >
            {m.goNext}
          </button>
        </div>
      )}
    </div>
  );
}

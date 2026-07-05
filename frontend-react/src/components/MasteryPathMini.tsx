import type { MasteryPathSnapshot } from "../api/types";
import { useLocale } from "../store/locale";

type Props = {
  path: MasteryPathSnapshot;
  compact?: boolean;
};

const PHASE_KEYS = ["incubate", "report", "paper", "masters", "reputation"] as const;

export default function MasteryPathMini({ path, compact = false }: Props) {
  const d = useLocale((s) => s.dict.masteryPathMini);
  const phases = path.phases.length ? path.phases : PHASE_KEYS.map((key) => ({ key, label: key, done: false }));

  return (
    <div className={compact ? "mt-2" : "mt-3"}>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-violet-700 dark:text-violet-300">
        {d.title} · {d.progress(path.done_count, path.total)}
      </p>
      <ol className={`mt-1.5 grid gap-1 ${compact ? "grid-cols-5" : "grid-cols-5 sm:grid-cols-5"}`}>
        {phases.map((phase) => {
          const label = d.phases[phase.key as keyof typeof d.phases] ?? phase.label;
          return (
            <li
              key={phase.key}
              title={label}
              className={`rounded px-1 py-1 text-center text-[9px] leading-tight ${
                phase.done
                  ? "bg-emerald-100 font-semibold text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200"
                  : "bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500"
              }`}
            >
              {phase.done ? "✓" : "·"}
              {!compact && <span className="mt-0.5 block truncate">{label}</span>}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

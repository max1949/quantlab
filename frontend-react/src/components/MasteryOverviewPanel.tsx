import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";

const DISMISS_KEY = "quantlab-mastery-overview-dismissed";

export default function MasteryOverviewPanel() {
  const d = useLocale((s) => s.dict.masteryOverview);
  const printRef = useRef<HTMLDivElement>(null);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const overview = journey.data?.mastery_overview;

  if (dismissed || journey.isLoading || !overview) return null;

  const printMap = () => {
    window.print();
  };

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div
      ref={printRef}
      className="card border border-violet-200 bg-gradient-to-r from-violet-50/80 to-fuchsia-50/40 print:border print:border-slate-300 print:bg-white dark:border-violet-900 dark:from-violet-950/30 dark:to-fuchsia-950/20"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between print:block">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-violet-700 dark:text-violet-300">
              {overview.title}
            </p>
            <span className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-800 dark:bg-violet-900/60 dark:text-violet-200">
              {d.progress(overview.done_count, overview.total)}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{overview.subtitle}</p>

          <ol className="mt-4 grid gap-2 sm:grid-cols-5 print:grid-cols-5">
            {overview.phases.map((phase, i) => {
              const isCurrent = i === overview.current_index && !phase.done;
              const content = (
                <>
                  {phase.done && "✓ "}
                  {phase.label}
                  {isCurrent && (
                    <span className="mt-1 block text-[10px] font-normal uppercase text-violet-600">
                      {overview.current_badge}
                    </span>
                  )}
                  <span className="mt-1 block text-[10px] font-normal opacity-80">{phase.hint}</span>
                  {!phase.done && (
                    <span className="mt-2 block text-[10px] font-semibold text-brand-600 print:hidden">
                      {d.open}
                    </span>
                  )}
                </>
              );
              return (
                <li
                  key={phase.key}
                  className={`rounded-lg border px-2 py-2 text-center text-xs print:border-slate-300 ${
                    phase.done
                      ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
                      : isCurrent
                        ? "border-violet-400 bg-white font-semibold text-violet-900 ring-2 ring-violet-300 dark:bg-slate-900 dark:text-violet-100"
                        : "border-slate-200 bg-white/50 text-slate-400 dark:border-slate-700 dark:bg-slate-900/30"
                  }`}
                >
                  {phase.done ? (
                    content
                  ) : (
                    <Link to={phase.cta_path} className="block hover:opacity-90">
                      {content}
                    </Link>
                  )}
                </li>
              );
            })}
          </ol>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2 print:hidden">
          <button type="button" className="btn-primary text-xs" onClick={printMap}>
            {d.print}
          </button>
          <button type="button" className="btn text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

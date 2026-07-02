import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { Spinner } from "./ui";

export default function ResearchJourneyRing() {
  const d = useLocale((s) => s.dict.dashboard);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: getResearchJourney });

  if (journey.isLoading) return <Spinner />;
  if (!journey.data) return null;

  const { done_count, total, steps, active_project_id } = journey.data;
  const pct = total > 0 ? Math.round((done_count / total) * 100) : 0;
  const next = steps.find((s) => !s.done);

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{d.journeyTitle}</h3>
          <p className="text-sm text-slate-500">{d.journeySubtitle}</p>
        </div>
        <span className="text-lg font-bold text-brand-600 dark:text-brand-400">
          {d.journeyProgress(done_count, total)}
        </span>
      </div>

      <div className="mb-4 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-brand-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>

      <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((s) => (
          <li
            key={s.key}
            className={`rounded-lg border px-2.5 py-2 text-xs ${
              s.done
                ? "border-emerald-200 bg-emerald-50/60 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200"
                : "border-slate-200 bg-slate-50/50 text-slate-600 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300"
            }`}
          >
            {s.done ? "✓ " : "○ "}
            {s.label}
          </li>
        ))}
      </ol>

      {next && (
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
          {d.journeyNext(next.label)}
          {active_project_id && next.key !== "template" && next.key !== "share" ? (
            <Link to={`/projects/${active_project_id}`} className="ml-2 text-brand-600 hover:underline">
              {d.journeyGoProject}
            </Link>
          ) : next.key === "template" ? (
            <Link to="/templates" className="ml-2 text-brand-600 hover:underline">
              {d.fromTemplate}
            </Link>
          ) : null}
        </p>
      )}
    </div>
  );
}

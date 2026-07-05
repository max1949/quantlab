import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useLocale } from "../store/locale";
import { Spinner } from "../components/ui";

const FALLBACK_STEP_KEYS = ["start", "validate", "report"] as const;

export default function BeginnerHandbookPage() {
  const h = useLocale((s) => s.dict.beginnerHandbook);
  const ov = useLocale((s) => s.dict.masteryOverview);
  const [params] = useSearchParams();
  const autoprint = params.get("print") === "1";

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const guide = journey.data?.quickstart_guide;
  const overview = journey.data?.mastery_overview;
  const sprint = journey.data?.beginner_sprint;

  useDocumentTitle(`${h.title} · QuantLab`);

  useEffect(() => {
    if (!autoprint || journey.isLoading) return;
    const t = window.setTimeout(() => window.print(), 400);
    return () => window.clearTimeout(t);
  }, [autoprint, journey.isLoading]);

  if (journey.isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center print:hidden">
        <Spinner />
      </div>
    );
  }

  const fallbackSteps = [
    { key: "start", label: h.step1Label, hint: h.step1Hint, done: false },
    { key: "validate", label: h.step2Label, hint: h.step2Hint, done: false },
    { key: "report", label: h.step3Label, hint: h.step3Hint, done: false },
  ];
  const quickSteps = guide?.steps ?? fallbackSteps;
  const phases = overview?.phases ?? [];

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 print:max-w-none print:px-8 print:py-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Link to="/app" className="text-sm text-brand-600 hover:underline">
          {h.backDashboard}
        </Link>
        <button type="button" className="btn-primary text-sm" onClick={() => window.print()}>
          {h.printPdf}
        </button>
      </div>

      <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm print:border-0 print:p-0 print:shadow-none dark:border-slate-700 dark:bg-slate-900">
        <header className="border-b border-slate-200 pb-4 print:border-slate-300">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">QuantLab AI</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-50">{h.title}</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{h.subtitle}</p>
          {overview && (
            <p className="mt-2 text-xs font-medium text-violet-700 dark:text-violet-300">
              {ov.progress(overview.done_count, overview.total)}
            </p>
          )}
        </header>

        <section className="mt-6">
          <h2 className="text-sm font-bold uppercase tracking-wide text-sky-800">{h.sectionQuickstart}</h2>
          <ol className="mt-3 space-y-3">
            {quickSteps.map((step, i) => (
              <li key={step.key ?? FALLBACK_STEP_KEYS[i]} className="flex gap-3 text-sm">
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    step.done ? "bg-emerald-500 text-white" : "bg-sky-500 text-white"
                  }`}
                >
                  {step.done ? "✓" : i + 1}
                </span>
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">{step.label}</p>
                  {step.hint && (
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{step.hint}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="mt-8">
          <h2 className="text-sm font-bold uppercase tracking-wide text-violet-800">{h.sectionMastery}</h2>
          {phases.length > 0 ? (
            <ol className="mt-3 grid gap-2 print:grid-cols-5 sm:grid-cols-5">
              {phases.map((phase, i) => {
                const isCurrent = overview ? i === overview.current_index && !phase.done : false;
                return (
                  <li
                    key={phase.key}
                    className={`rounded-lg border px-2 py-2 text-center text-xs print:border-slate-400 ${
                      phase.done
                        ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                        : isCurrent
                          ? "border-violet-400 bg-violet-50 font-semibold text-violet-900"
                          : "border-slate-200 text-slate-500"
                    }`}
                  >
                    {phase.done && "✓ "}
                    {phase.label}
                    <span className="mt-1 block text-[10px] font-normal opacity-80">{phase.hint}</span>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="mt-2 text-sm text-slate-500">
              {h.masteryFallback(journey.data?.done_count ?? 0, journey.data?.total ?? 7)}
            </p>
          )}
        </section>

        {sprint && (
          <section className="mt-8">
            <h2 className="text-sm font-bold uppercase tracking-wide text-amber-800">{h.sectionSprint}</h2>
            <p className="mt-2 text-sm font-medium text-slate-800 dark:text-slate-100">{sprint.title}</p>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{sprint.message}</p>
          </section>
        )}

        <footer className="mt-8 border-t border-slate-200 pt-4 text-xs text-slate-500 print:border-slate-300">
          <p>{h.footer}</p>
          <p className="mt-2 print:hidden">{h.printHint}</p>
        </footer>
      </article>
    </div>
  );
}

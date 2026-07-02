import { useLocale } from "../store/locale";

export default function FactorFormulaGuide({ compact }: { compact?: boolean }) {
  const g = useLocale((s) => s.dict.factorGuide);

  return (
    <div
      className={`rounded-xl border border-brand-100 bg-brand-50/40 p-4 dark:border-brand-900 dark:bg-brand-950/30 ${
        compact ? "mb-3" : "mb-4"
      }`}
    >
      <h4 className="font-semibold text-brand-800 dark:text-brand-200">{g.title}</h4>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{g.intro}</p>

      <ol className="mt-3 space-y-3 text-sm text-slate-700 dark:text-slate-200">
        {g.lessons.map((lesson, i) => (
          <li key={lesson.title}>
            <p className="font-medium">
              {i + 1}. {lesson.title}
            </p>
            <p className="mt-0.5 text-slate-600 dark:text-slate-300">{lesson.body}</p>
            {lesson.example && (
              <code className="mt-1 block rounded bg-white/80 px-2 py-1 font-mono text-xs text-brand-700 dark:bg-slate-900/60 dark:text-brand-300">
                {lesson.example}
              </code>
            )}
          </li>
        ))}
      </ol>

      <p className="mt-3 text-xs text-slate-500">{g.tip}</p>
    </div>
  );
}

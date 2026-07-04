import { useLocale } from "../store/locale";

type Tip = {
  title: string;
  tip: string;
  action: string;
};

type Props = {
  tips: Tip[];
  onAction: (action: string) => void;
};

export default function FailureCoachPanel({ tips, onAction }: Props) {
  const f = useLocale((s) => s.dict.failureCoach);
  if (!tips.length) return null;

  return (
    <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50/80 p-4 dark:border-amber-900 dark:bg-amber-950/30">
      <p className="mb-2 font-semibold text-amber-900 dark:text-amber-100">{f.title}</p>
      <p className="mb-3 text-xs text-amber-800/80 dark:text-amber-200/80">{f.subtitle}</p>
      <ul className="space-y-3">
        {tips.map((item) => (
          <li
            key={`${item.action}-${item.title}`}
            className="rounded-lg border border-amber-100 bg-white/70 px-3 py-2 text-sm dark:border-amber-900 dark:bg-slate-900/40"
          >
            <p className="font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{item.tip}</p>
            <button
              type="button"
              className="btn mt-2 text-xs"
              onClick={() => onAction(item.action)}
            >
              {f.fixCta}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

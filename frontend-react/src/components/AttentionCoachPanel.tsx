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

export default function AttentionCoachPanel({ tips, onAction }: Props) {
  const j = useLocale((s) => s.dict.jointAttentionCoach);
  if (!tips.length) return null;

  return (
    <div className="mb-4 rounded-xl border border-rose-200 bg-gradient-to-r from-rose-50/80 to-violet-50/60 p-4 dark:border-rose-900 dark:from-rose-950/30 dark:to-violet-950/20">
      <p className="mb-2 font-semibold text-rose-900 dark:text-rose-100">{j.title}</p>
      <p className="mb-3 text-xs text-rose-800/80 dark:text-rose-200/80">{j.subtitle}</p>
      <ul className="space-y-3">
        {tips.map((item) => (
          <li
            key={`${item.action}-${item.title}`}
            className="rounded-lg border border-rose-100 bg-white/70 px-3 py-2 text-sm dark:border-rose-900 dark:bg-slate-900/40"
          >
            <p className="font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{item.tip}</p>
            <button
              type="button"
              className="btn mt-2 text-xs"
              onClick={() => onAction(item.action)}
            >
              {item.action === "templates" ? j.ctaTemplates : j.ctaRevalidate}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

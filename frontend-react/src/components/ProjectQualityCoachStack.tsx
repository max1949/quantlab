import { useState } from "react";
import { useLocale } from "../store/locale";

type Tip = {
  title: string;
  tip: string;
  action: string;
};

type QualityTip = Tip & { kind: "attention" | "failure" };

const EXPAND_KEY = "quantlab-project-quality-coach-expanded";

type Props = {
  attentionTips: Tip[];
  failureTips: Tip[];
  onAction: (action: string) => void;
};

function mergeTips(attentionTips: Tip[], failureTips: Tip[]): QualityTip[] {
  return [
    ...attentionTips.map((t) => ({ ...t, kind: "attention" as const })),
    ...failureTips.map((t) => ({ ...t, kind: "failure" as const })),
  ];
}

function TipCard({
  item,
  onAction,
}: {
  item: QualityTip;
  onAction: (action: string) => void;
}) {
  const j = useLocale((s) => s.dict.jointAttentionCoach);
  const f = useLocale((s) => s.dict.failureCoach);
  const labels = useLocale((s) => s.dict.qualityCoachLabels);
  const isAttention = item.kind === "attention";

  return (
    <div
      className={`rounded-lg border px-3 py-2 text-sm ${
        isAttention
          ? "border-rose-100 bg-white/70 dark:border-rose-900 dark:bg-slate-900/40"
          : "border-amber-100 bg-white/70 dark:border-amber-900 dark:bg-slate-900/40"
      }`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {labels[item.kind]}
      </p>
      <p className="mt-1 font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
      <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{item.tip}</p>
      <button type="button" className="btn mt-2 text-xs" onClick={() => onAction(item.action)}>
        {isAttention
          ? item.action === "templates"
            ? j.ctaTemplates
            : j.ctaRevalidate
          : f.fixCta}
      </button>
    </div>
  );
}

export default function ProjectQualityCoachStack({ attentionTips, failureTips, onAction }: Props) {
  const j = useLocale((s) => s.dict.jointAttentionCoach);
  const f = useLocale((s) => s.dict.failureCoach);
  const p = useLocale((s) => s.dict.projectDetail);
  const [expanded, setExpanded] = useState(() => localStorage.getItem(EXPAND_KEY) === "1");

  const tips = mergeTips(attentionTips, failureTips);
  if (tips.length === 0) return null;

  const hasAttention = attentionTips.length > 0;
  const shellClass = hasAttention
    ? "mb-4 rounded-xl border border-rose-200 bg-gradient-to-r from-rose-50/80 to-violet-50/60 p-4 dark:border-rose-900 dark:from-rose-950/30 dark:to-violet-950/20"
    : "mb-4 rounded-xl border border-amber-200 bg-amber-50/80 p-4 dark:border-amber-900 dark:bg-amber-950/30";

  const needsFold = tips.length > 1;
  const visible = expanded || !needsFold ? tips : tips.slice(0, 1);
  const hidden = expanded || !needsFold ? [] : tips.slice(1);

  return (
    <div className={shellClass}>
      <p
        className={`mb-2 font-semibold ${
          hasAttention ? "text-rose-900 dark:text-rose-100" : "text-amber-900 dark:text-amber-100"
        }`}
      >
        {hasAttention ? j.title : f.title}
      </p>
      <p
        className={`mb-3 text-xs ${
          hasAttention ? "text-rose-800/80 dark:text-rose-200/80" : "text-amber-800/80 dark:text-amber-200/80"
        }`}
      >
        {hasAttention ? j.subtitle : f.subtitle}
      </p>

      <ul className="space-y-3">
        {visible.map((item) => (
          <li key={`${item.kind}-${item.action}-${item.title}`}>
            <TipCard item={item} onAction={onAction} />
          </li>
        ))}
      </ul>

      {hidden.length > 0 && (
        <div className="mt-3 rounded-lg border border-dashed border-slate-200 bg-white/50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900/30">
          <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
            {p.qualityCoachMore(hidden.length)}
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-500 dark:text-slate-400">
            {hidden.map((item) => (
              <li key={`fold-${item.kind}-${item.action}-${item.title}`} className="truncate">
                {item.title}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="btn mt-3 text-xs"
            onClick={() => {
              setExpanded(true);
              localStorage.setItem(EXPAND_KEY, "1");
            }}
          >
            {p.qualityCoachExpand}
          </button>
        </div>
      )}

      {needsFold && expanded && (
        <button
          type="button"
          className="mt-3 text-xs font-medium text-slate-500 hover:text-brand-600"
          onClick={() => {
            setExpanded(false);
            localStorage.removeItem(EXPAND_KEY);
          }}
        >
          {p.qualityCoachCollapse}
        </button>
      )}
    </div>
  );
}

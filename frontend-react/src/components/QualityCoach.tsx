import { Link } from "react-router-dom";
import { useLocale } from "../store/locale";

type Props = {
  reasons: string[];
  onScrollToFactorLab: () => void;
  onRunValidation?: () => void;
  canRunValidation: boolean;
  showDataPlanHint?: boolean;
};

type TipKey = "validation" | "oos" | "robustness" | "backtest" | "holdout" | "generic";

function classifyReason(reason: string): TipKey {
  if (reason.includes("科学验证") || reason.includes("validation")) return "validation";
  if (reason.includes("样本外") || reason.includes("OOS")) return "oos";
  if (reason.includes("稳健性")) return "robustness";
  if (reason.includes("回测")) return "backtest";
  if (reason.includes("holdout") || reason.includes("封印")) return "holdout";
  return "generic";
}

export default function QualityCoach({
  reasons,
  onScrollToFactorLab,
  onRunValidation,
  canRunValidation,
  showDataPlanHint,
}: Props) {
  const c = useLocale((s) => s.dict.qualityCoach);
  if (!reasons.length) return null;

  const seen = new Set<TipKey>();
  const tips: TipKey[] = [];
  for (const r of reasons) {
    const k = classifyReason(r);
    if (!seen.has(k)) {
      seen.add(k);
      tips.push(k);
    }
  }

  return (
    <div className="mt-4 rounded-lg border border-brand-200 bg-white/60 p-4 dark:border-brand-900 dark:bg-slate-900/40">
      <p className="mb-3 font-medium text-slate-800 dark:text-slate-100">{c.title}</p>
      {showDataPlanHint && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          <p>{c.dataPlanNote}</p>
          <Link to="/pricing" className="mt-2 inline-block text-xs font-medium text-brand-600 hover:underline">
            {c.upgradeData}
          </Link>
        </div>
      )}
      <ul className="space-y-3">
        {tips.map((key) => (
          <li key={key} className="text-sm text-slate-600 dark:text-slate-300">
            <p>{c.tips[key]}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {(key === "oos" || key === "robustness" || key === "backtest" || key === "generic") && (
                <button type="button" className="btn text-xs" onClick={onScrollToFactorLab}>
                  {c.adjustFactor}
                </button>
              )}
              {key === "validation" && canRunValidation && onRunValidation && (
                <button type="button" className="btn-primary text-xs" onClick={onRunValidation}>
                  {c.runValidation}
                </button>
              )}
              {key === "holdout" && (
                <Link to="/pricing" className="btn text-xs">
                  {c.upgradeData}
                </Link>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import HandbookExportButtons from "./HandbookExportButtons";

const DISMISS_KEY = "quantlab-handbook-strip-dismissed";

export default function BeginnerHandbookStrip() {
  const h = useLocale((s) => s.dict.beginnerHandbook);
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "1");
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  if (dismissed || journey.isLoading || !journey.data) return null;

  const j = journey.data;
  const masteryDone = j.mastery_overview == null && j.done_count >= j.total;
  if (masteryDone) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="card flex flex-col gap-3 border border-indigo-200 bg-indigo-50/50 sm:flex-row sm:items-center sm:justify-between dark:border-indigo-900 dark:bg-indigo-950/30">
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
          📄 {h.title}
        </p>
        <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{h.stripHint}</p>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        <HandbookExportButtons compact />
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {h.stripDismiss}
        </button>
      </div>
    </div>
  );
}

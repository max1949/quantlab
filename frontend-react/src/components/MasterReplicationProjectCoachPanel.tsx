import { useEffect, useState } from "react";
import { FOLLOWING_PROJECT_REPLICATION_KEY } from "../lib/onboardingFocus";
import { burstConfetti } from "../lib/confetti";
import { useLocale } from "../store/locale";

function dismissKey(projectId: string) {
  return `quantlab-master-replication-coach-${projectId}`;
}

type Props = {
  projectId: string;
  backtestDone: boolean;
  backtestPending: boolean;
  onRunBacktest: () => void;
};

export default function MasterReplicationProjectCoachPanel({
  projectId,
  backtestDone,
  backtestPending,
  onRunBacktest,
}: Props) {
  const d = useLocale((s) => s.dict.masterReplicationProjectCoach);
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(dismissKey(projectId)) === "1",
  );
  const [fresh, setFresh] = useState(
    () =>
      typeof window !== "undefined" &&
      sessionStorage.getItem(FOLLOWING_PROJECT_REPLICATION_KEY) === projectId,
  );

  const matches = fresh && !backtestDone && !dismissed;

  useEffect(() => {
    if (!matches) return;
    sessionStorage.removeItem(FOLLOWING_PROJECT_REPLICATION_KEY);
    burstConfetti(2000);
    const scrollTimer = window.setTimeout(() => {
      document.getElementById("project-step-backtest")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 200);
    return () => window.clearTimeout(scrollTimer);
  }, [matches]);

  if (!matches) return null;

  const dismiss = () => {
    localStorage.setItem(dismissKey(projectId), "1");
    setDismissed(true);
    setFresh(false);
  };

  return (
    <div className="mb-4 card border border-teal-200 bg-gradient-to-r from-teal-50/90 to-cyan-50/60 dark:border-teal-900 dark:from-teal-950/40 dark:to-cyan-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-teal-800 dark:text-teal-200">
        📖 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <p className="mt-2 text-xs text-teal-900/80 dark:text-teal-100/80">{d.stepHint}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="btn-primary text-xs"
          disabled={backtestPending}
          onClick={() => {
            dismiss();
            onRunBacktest();
          }}
        >
          {backtestPending ? d.running : d.runBacktest}
        </button>
        <button type="button" className="btn text-xs" onClick={dismiss}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

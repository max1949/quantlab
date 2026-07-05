import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { burstConfetti } from "../lib/confetti";
import {
  clearReplicationBenchmark,
  loadReplicationBenchmark,
  replicationBacktestDismissKey,
  replicationValidationDismissKey,
  type ReplicationBenchmark,
} from "../lib/replicationBenchmark";
import { REPLICATION_REPORT_PENDING_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

type Props = {
  projectId: string;
  backtestDone: boolean;
  validationDone: boolean;
  reportDone: boolean;
  yourBacktestSharpe: number | null | undefined;
  yourOosSharpe: number | null | undefined;
  yourRobustness: number | null | undefined;
  onRunValidation: () => void;
  onGenerateReport: () => void;
};

function compareVerdict(
  master: number | null,
  yours: number | null | undefined,
  d: {
    noMasterMetric: string;
    beat: (master: string, yours: string) => string;
    close: (master: string, yours: string) => string;
    gap: (master: string, yours: string) => string;
  },
  opts: { beatDelta: number; closeDelta: number },
): string {
  if (master == null || yours == null) return d.noMasterMetric;
  const m = master.toFixed(2);
  const y = yours.toFixed(2);
  const delta = yours - master;
  if (delta >= opts.beatDelta) return d.beat(m, y);
  if (delta >= opts.closeDelta) return d.close(m, y);
  return d.gap(m, y);
}

export default function MasterReplicationBenchmarkPanel({
  projectId,
  backtestDone,
  validationDone,
  reportDone,
  yourBacktestSharpe,
  yourOosSharpe,
  yourRobustness,
  onRunValidation,
  onGenerateReport,
}: Props) {
  const d = useLocale((s) => s.dict.masterReplicationBenchmark);
  const [benchmark] = useState(() => loadReplicationBenchmark(projectId));
  const [backtestDismissed, setBacktestDismissed] = useState(
    () => localStorage.getItem(replicationBacktestDismissKey(projectId)) === "1",
  );
  const [validationDismissed, setValidationDismissed] = useState(
    () => localStorage.getItem(replicationValidationDismissKey(projectId)) === "1",
  );
  const [celebratedBacktest, setCelebratedBacktest] = useState(false);
  const [celebratedOos, setCelebratedOos] = useState(false);

  const showBacktest =
    Boolean(benchmark && backtestDone && !validationDone && !backtestDismissed);
  const showValidation =
    Boolean(benchmark && validationDone && !reportDone && !validationDismissed);

  useEffect(() => {
    if (!showBacktest || celebratedBacktest || benchmark?.oos_sharpe == null || yourBacktestSharpe == null) {
      return;
    }
    if (yourBacktestSharpe - benchmark.oos_sharpe >= 0.05) {
      burstConfetti(2400);
      setCelebratedBacktest(true);
    }
  }, [showBacktest, celebratedBacktest, benchmark, yourBacktestSharpe]);

  useEffect(() => {
    if (!showValidation || celebratedOos || benchmark?.oos_sharpe == null || yourOosSharpe == null) {
      return;
    }
    if (yourOosSharpe >= benchmark.oos_sharpe) {
      burstConfetti(3200);
      setCelebratedOos(true);
    }
  }, [showValidation, celebratedOos, benchmark, yourOosSharpe]);

  useEffect(() => {
    if (!reportDone || !benchmark) return;
    clearReplicationBenchmark(projectId);
  }, [reportDone, benchmark, projectId]);

  if (!benchmark || (!showBacktest && !showValidation)) return null;

  const masterLabel = benchmark.owner_username
    ? d.masterNamed(benchmark.owner_username)
    : d.masterGeneric;

  const dismissBacktest = () => {
    localStorage.setItem(replicationBacktestDismissKey(projectId), "1");
    setBacktestDismissed(true);
  };

  const finalizeReplication = () => {
    localStorage.setItem(replicationValidationDismissKey(projectId), "1");
    clearReplicationBenchmark(projectId);
    setValidationDismissed(true);
  };

  if (showBacktest) {
    return (
      <div className="mb-4 card border border-amber-200 bg-gradient-to-r from-amber-50/90 to-orange-50/60 dark:border-amber-900 dark:from-amber-950/40 dark:to-orange-950/30">
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-200">
          📊 {d.badge}
        </p>
        <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {compareVerdict(benchmark.oos_sharpe, yourBacktestSharpe, {
            noMasterMetric: d.noMasterMetric,
            beat: d.beat,
            close: d.close,
            gap: d.gap,
          }, { beatDelta: 0.05, closeDelta: -0.2 })}
        </p>
        <MetricChips
          d={d}
          benchmark={benchmark}
          primary={yourBacktestSharpe}
          primaryLabel={(v) => d.yourBacktest(v)}
          yourRobustness={yourRobustness}
        />
        <p className="mt-2 text-xs text-amber-900/80 dark:text-amber-100/80">{d.nextStep}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link to={`/reports/${benchmark.report_id}`} className="btn text-xs" onClick={dismissBacktest}>
            {masterLabel}
          </Link>
          <button
            type="button"
            className="btn-primary text-xs"
            onClick={() => {
              dismissBacktest();
              onRunValidation();
            }}
          >
            {d.runValidation}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4 card border border-emerald-200 bg-gradient-to-r from-emerald-50/90 to-teal-50/60 dark:border-emerald-900 dark:from-emerald-950/40 dark:to-teal-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
        🎯 {d.oosBadge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.oosTitle}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        {compareVerdict(benchmark.oos_sharpe, yourOosSharpe, {
          noMasterMetric: d.oosNoMetric,
          beat: d.oosBeat,
          close: d.oosClose,
          gap: d.oosGap,
        }, { beatDelta: 0, closeDelta: -0.15 })}
      </p>
      <MetricChips
        d={d}
        benchmark={benchmark}
        primary={yourOosSharpe}
        primaryLabel={(v) => d.yourOos(v)}
        yourRobustness={yourRobustness}
      />
      <p className="mt-2 text-xs text-emerald-900/80 dark:text-emerald-100/80">{d.oosNextStep}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to={`/reports/${benchmark.report_id}`} className="btn text-xs">
          {masterLabel}
        </Link>
        <button
          type="button"
          className="btn-primary text-xs"
          onClick={() => {
            sessionStorage.setItem(REPLICATION_REPORT_PENDING_KEY, projectId);
            finalizeReplication();
            onGenerateReport();
          }}
        >
          {d.generateReport}
        </button>
        <button type="button" className="btn text-xs" onClick={finalizeReplication}>
          {d.dismiss}
        </button>
      </div>
    </div>
  );
}

function MetricChips({
  d,
  benchmark,
  primary,
  primaryLabel,
  yourRobustness,
}: {
  d: {
    masterOos: (v: string) => string;
    robustnessCompare: (master: string, yours: string) => string;
  };
  benchmark: ReplicationBenchmark;
  primary: number | null | undefined;
  primaryLabel: (v: string) => string;
  yourRobustness: number | null | undefined;
}) {
  return (
    <div className="mt-3 flex flex-wrap gap-2 text-xs">
      {benchmark.oos_sharpe != null && (
        <span className="rounded-full bg-amber-100 px-2.5 py-1 font-medium text-amber-900 dark:bg-amber-950/50 dark:text-amber-100">
          {d.masterOos(benchmark.oos_sharpe.toFixed(2))}
        </span>
      )}
      {primary != null && (
        <span className="rounded-full bg-white px-2.5 py-1 font-medium text-slate-800 ring-1 ring-amber-200 dark:bg-slate-900 dark:text-slate-100 dark:ring-amber-800">
          {primaryLabel(primary.toFixed(2))}
        </span>
      )}
      {benchmark.robustness_score != null && yourRobustness != null && (
        <span className="rounded-full bg-orange-100 px-2.5 py-1 font-medium text-orange-900 dark:bg-orange-950/50 dark:text-orange-100">
          {d.robustnessCompare(
            benchmark.robustness_score.toFixed(0),
            yourRobustness.toFixed(0),
          )}
        </span>
      )}
    </div>
  );
}

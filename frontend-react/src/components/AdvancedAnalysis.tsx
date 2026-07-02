import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getEntitlements,
  runCostSensitivity,
  runCrossSectionBacktest,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import type { Dictionary } from "../i18n/dictionaries";
import type {
  CostSensitivity,
  CrossSectionBacktest,
  FeatureState,
} from "../api/types";

export default function AdvancedAnalysis({
  projectId,
  factorId,
  symbol,
}: {
  projectId: string;
  factorId: string | null;
  symbol: string;
}) {
  const notify = useUi((s) => s.notify);
  const l2 = useLocale((s) => s.dict.l2Analysis);
  const lk = useLocale((s) => s.dict.locked);
  const c = useLocale((s) => s.dict.common);
  const ent = useQuery({ queryKey: ["entitlements"], queryFn: getEntitlements });
  const crossFeat = ent.data?.features.find((f) => f.key === "backtest_cross_section");
  const costFeat = ent.data?.features.find((f) => f.key === "cost_sensitivity");

  const cross = useMutation({
    mutationFn: () =>
      runCrossSectionBacktest({
        factor_id: factorId!,
        symbols: ["RB", "AU", "IF"],
        top_n: 1,
        long_short: true,
      }),
    onSuccess: () => {
      void trackEvent("cross_section_backtest_run", { project: projectId });
      notify(l2.crossDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l2.crossFail), "error"),
  });

  const cost = useMutation({
    mutationFn: () =>
      runCostSensitivity({
        factor_id: factorId!,
        symbol,
        fee_rates: [0, 0.0002, 0.0005, 0.001],
        slippage_bps_values: [0, 1, 3, 5],
      }),
    onSuccess: () => {
      void trackEvent("cost_sensitivity_run", { project: projectId, symbol });
      notify(l2.costDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l2.costFail), "error"),
  });

  return (
    <div className="card">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{l2.title}</h3>
          <p className="text-sm text-slate-500">{l2.subtitle}</p>
        </div>
        <span className="badge">{l2.badge}</span>
      </div>

      {!factorId ? (
        <p className="text-sm text-slate-400">{l2.needFactor}</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <AnalysisBox
            title={l2.crossTitle}
            desc={l2.crossDesc}
            feat={crossFeat}
            running={cross.isPending}
            button={l2.crossBtn}
            onRun={() => cross.mutate()}
            lk={lk}
            c={c}
          >
            {cross.data && <CrossSectionResult data={cross.data} l2={l2} />}
          </AnalysisBox>

          <AnalysisBox
            title={l2.costTitle}
            desc={l2.costDesc(symbol)}
            feat={costFeat}
            running={cost.isPending}
            button={l2.costBtn}
            onRun={() => cost.mutate()}
            lk={lk}
            c={c}
          >
            {cost.data && <CostResult data={cost.data} l2={l2} />}
          </AnalysisBox>
        </div>
      )}
    </div>
  );
}

function AnalysisBox({
  title,
  desc,
  feat,
  running,
  button,
  onRun,
  children,
  lk,
  c,
}: {
  title: string;
  desc: string;
  feat?: FeatureState;
  running: boolean;
  button: string;
  onRun: () => void;
  children: React.ReactNode;
  lk: Dictionary["locked"];
  c: Dictionary["common"];
}) {
  const locked = feat && !feat.allowed;
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/40">
      <div className="mb-3">
        <h4 className="font-medium text-slate-800 dark:text-slate-100">
          {title} {locked && "🔒"}
        </h4>
        <p className="text-sm text-slate-500">{desc}</p>
      </div>
      {locked ? (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
          <p className="mb-2">
            {lk.needLevelTier(feat.min_level_name, feat.min_tier_name)}
          </p>
          <Link to="/pricing" className="btn-primary inline-block">
            {c.upgradePlans}
          </Link>
        </div>
      ) : (
        <>
          <button className="btn-primary" disabled={running} onClick={onRun}>
            {running ? lk.running : button}
          </button>
          {children}
        </>
      )}
    </div>
  );
}

function CrossSectionResult({
  data,
  l2,
}: {
  data: CrossSectionBacktest;
  l2: Dictionary["l2Analysis"];
}) {
  return (
    <div className="mt-4 space-y-3 text-sm">
      <MetricGrid metrics={data.metrics} l2={l2} />
      <div>
        <p className="mb-1 text-xs font-medium text-slate-400">{l2.latestHoldings}</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(data.latest_weights).map(([s, w]) => (
            <span key={s} className="badge">
              {s}: {fmtPct(w)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function CostResult({
  data,
  l2,
}: {
  data: CostSensitivity;
  l2: Dictionary["l2Analysis"];
}) {
  const allNegative = data.results.every(
    (r) => r.metrics.annual_return == null || r.metrics.annual_return < 0,
  );

  return (
    <div className="mt-4 space-y-2">
      <p className="text-xs text-slate-500 dark:text-slate-400">{l2.costSummary(data.results.length)}</p>
      {allNegative && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          {l2.costAllNegative}
        </p>
      )}
      <div className="overflow-x-auto text-xs">
        <table className="min-w-full border-separate border-spacing-y-1">
          <thead className="text-slate-500 dark:text-slate-400">
            <tr>
              <th className="px-2 py-1 text-left font-medium">{l2.fee}</th>
              <th className="px-2 py-1 text-left font-medium">{l2.slippage}</th>
              <th className="px-2 py-1 text-left font-medium">{l2.annual}</th>
              <th className="px-2 py-1 text-left font-medium">{l2.sharpe}</th>
              <th className="px-2 py-1 text-left font-medium">{l2.drawdown}</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((r) => {
              const neg = (r.metrics.annual_return ?? 0) < 0;
              return (
                <tr
                  key={`${r.fee_rate}-${r.slippage_bps}`}
                  className="text-slate-800 dark:text-slate-100"
                >
                  <td className="rounded-l bg-white px-2 py-1.5 dark:bg-slate-800">{fmtPct(r.fee_rate)}</td>
                  <td className="bg-white px-2 py-1.5 dark:bg-slate-800">{r.slippage_bps}bp</td>
                  <td
                    className={`bg-white px-2 py-1.5 font-medium dark:bg-slate-800 ${
                      neg ? "text-rose-600 dark:text-rose-400" : "text-emerald-700 dark:text-emerald-400"
                    }`}
                  >
                    {fmtPct(r.metrics.annual_return)}
                  </td>
                  <td className="bg-white px-2 py-1.5 dark:bg-slate-800">{fmtNum(r.metrics.sharpe)}</td>
                  <td className="rounded-r bg-white px-2 py-1.5 dark:bg-slate-800">
                    {fmtPct(r.metrics.max_drawdown)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MetricGrid({
  metrics,
  l2,
}: {
  metrics: Record<string, number | null>;
  l2: Dictionary["l2Analysis"];
}) {
  const items = [
    [l2.totalReturn, fmtPct(metrics.total_return)],
    [l2.annual, fmtPct(metrics.annual_return)],
    [l2.sharpe, fmtNum(metrics.sharpe)],
    [l2.maxDrawdown, fmtPct(metrics.max_drawdown)],
  ];
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(([k, v]) => (
        <div key={k} className="rounded-lg bg-white px-3 py-2 dark:bg-slate-800">
          <div className="text-xs text-slate-500 dark:text-slate-400">{k}</div>
          <div className="font-semibold text-slate-800 dark:text-slate-100">{v}</div>
        </div>
      ))}
    </div>
  );
}

function fmtNum(v: number | null | undefined) {
  return v === null || v === undefined ? "—" : Number(v).toFixed(2);
}

function fmtPct(v: number | null | undefined) {
  return v === null || v === undefined ? "—" : `${(Number(v) * 100).toFixed(2)}%`;
}

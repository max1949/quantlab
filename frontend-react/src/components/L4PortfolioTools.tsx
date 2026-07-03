import { Link } from "react-router-dom";
import PaperExecutionPanel from "./PaperExecutionPanel";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getEntitlements,
  optimizePortfolio,
  paperSimulate,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import type { Dictionary } from "../i18n/dictionaries";
import type { FeatureState, PaperSimulate, PortfolioOptimize } from "../api/types";

const SYMBOLS = ["RB", "AU", "IF"];

export default function L4PortfolioTools({ projectId }: { projectId: string }) {
  const notify = useUi((s) => s.notify);
  const l4 = useLocale((s) => s.dict.l4Tools);
  const c = useLocale((s) => s.dict.common);
  const ent = useQuery({ queryKey: ["entitlements"], queryFn: getEntitlements });
  const optFeat = ent.data?.features.find((f) => f.key === "portfolio_optimize");
  const paperFeat = ent.data?.features.find((f) => f.key === "paper_trading");

  const opt = useMutation({
    mutationFn: () => optimizePortfolio({ symbols: SYMBOLS, method: "risk_parity" }),
    onSuccess: () => {
      void trackEvent("portfolio_optimize_run", { project: projectId });
      notify(l4.optimizeDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l4.optimizeFail), "error"),
  });

  const paper = useMutation({
    mutationFn: () =>
      paperSimulate({
        symbols: SYMBOLS,
        weights: cleanWeights(opt.data?.weights ?? {}),
        rebalance: "monthly",
      }),
    onSuccess: () => {
      void trackEvent("paper_simulate_run", { project: projectId });
      notify(l4.paperDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l4.paperFail), "error"),
  });

  const locked = (optFeat && !optFeat.allowed) || (paperFeat && !paperFeat.allowed);

  return (
    <div className="card">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{l4.title}</h3>
          <p className="text-sm text-slate-500">{l4.subtitle}</p>
        </div>
        <span className="badge">{l4.badge}</span>
      </div>

      {locked ? (
        <Locked feat={optFeat && !optFeat.allowed ? optFeat : paperFeat} l4={l4} c={c} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <h4 className="font-medium">{l4.optimizeTitle}</h4>
            <p className="mb-3 text-sm text-slate-500">{l4.optimizeDesc}</p>
            <button className="btn-primary" disabled={opt.isPending} onClick={() => opt.mutate()}>
              {opt.isPending ? l4.optimizing : l4.optimizeBtn}
            </button>
            {opt.data && <OptimizeResult data={opt.data} l4={l4} />}
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <h4 className="font-medium">{l4.paperTitle}</h4>
            <p className="mb-3 text-sm text-slate-500">{l4.paperDesc}</p>
            <button
              className="btn-primary"
              disabled={paper.isPending || !opt.data}
              onClick={() => paper.mutate()}
            >
              {paper.isPending ? l4.simulating : l4.paperBtn}
            </button>
            {paper.data && <PaperResult data={paper.data} l4={l4} />}
          </div>
        </div>
      )}
      {!locked && <PaperExecutionPanel />}
    </div>
  );
}

function Locked({
  feat,
  l4,
  c,
}: {
  feat?: FeatureState;
  l4: Dictionary["l4Tools"];
  c: Dictionary["common"];
}) {
  return (
    <div className="rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
      <p className="mb-2">
        {l4.needLevelTier(feat?.min_level_name ?? "L4", feat?.min_tier_name ?? "Pro")}
      </p>
      <Link to="/pricing" className="btn-primary inline-block">
        {c.upgradePlans}
      </Link>
    </div>
  );
}

function OptimizeResult({ data, l4 }: { data: PortfolioOptimize; l4: Dictionary["l4Tools"] }) {
  return (
    <div className="mt-4 space-y-3 text-sm">
      <MetricGrid metrics={data.expected} l4={l4} />
      <div>
        <p className="mb-1 text-xs font-medium text-slate-400">{l4.suggestedWeights}</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(data.weights).map(([s, w]) => (
            <span key={s} className="badge">
              {s}: {fmtPct(w)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function PaperResult({ data, l4 }: { data: PaperSimulate; l4: Dictionary["l4Tools"] }) {
  return (
    <div className="mt-4 text-sm">
      <MetricGrid metrics={data.metrics} l4={l4} />
    </div>
  );
}

function MetricGrid({
  metrics,
  l4,
}: {
  metrics: Record<string, number | null>;
  l4: Dictionary["l4Tools"];
}) {
  const items = [
    [l4.annual, fmtPct(metrics.annual_return)],
    [l4.volatility, fmtPct(metrics.annual_volatility)],
    [l4.sharpe, fmtNum(metrics.sharpe)],
    [l4.drawdown, fmtPct(metrics.max_drawdown)],
  ];
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(([k, v]) => (
        <div key={k} className="rounded-lg bg-white px-3 py-2">
          <div className="text-xs text-slate-400">{k}</div>
          <div className="font-semibold text-slate-800">{v}</div>
        </div>
      ))}
    </div>
  );
}

function cleanWeights(weights: Record<string, number | null>) {
  return Object.fromEntries(Object.entries(weights).map(([k, v]) => [k, Number(v ?? 0)]));
}

function fmtNum(v: number | null | undefined) {
  return v === null || v === undefined ? "—" : Number(v).toFixed(2);
}

function fmtPct(v: number | null | undefined) {
  return v === null || v === undefined ? "—" : `${(Number(v) * 100).toFixed(1)}%`;
}

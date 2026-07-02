import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getBacktest, listBacktests, summarizeBacktest } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { Spinner } from "./ui";

type Props = {
  factorId: string | null;
  enabled: boolean;
};

const MIN_SHARPE_HINT = 0.3;

export default function BacktestResultsPanel({ factorId, enabled }: Props) {
  const v = useLocale((s) => s.dict.backtestPanel);
  const ai = useLocale((s) => s.dict.aiReview);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();
  const setUser = useAuth((s) => s.setUser);
  const [insight, setInsight] = useState<string | null>(null);
  const syncedBacktest = useRef<string | null>(null);

  const list = useQuery({
    queryKey: ["backtests"],
    queryFn: listBacktests,
    enabled: enabled && Boolean(factorId),
  });

  const latestId =
    list.data
      ?.filter((x) => x.factor_id === factorId && x.status === "success")
      .sort((a, b) => b.created_at.localeCompare(a.created_at))[0]?.id ?? null;

  const detail = useQuery({
    queryKey: ["backtest", latestId],
    queryFn: () => getBacktest(latestId!),
    enabled: Boolean(latestId),
  });

  useEffect(() => {
    if (!latestId || detail.data?.status !== "success") return;
    if (syncedBacktest.current === latestId) return;
    syncedBacktest.current = latestId;
    void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
    void useAuth.getState().refreshMe().then((me) => {
      if (me) setUser(me);
    });
  }, [latestId, detail.data?.status, qc, setUser]);

  const aiSummary = useMutation({
    mutationFn: () => summarizeBacktest(latestId!),
    onSuccess: (res) => {
      setInsight(res.content);
      notify(ai.done, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, ai.fail), "error"),
  });

  if (!enabled || !factorId) return null;
  if (list.isLoading) return <Spinner />;
  if (!latestId) {
    return (
      <div className="card border-slate-200 bg-slate-50/40 dark:border-slate-700 dark:bg-slate-900/30">
        <p className="text-sm text-slate-500">{v.empty}</p>
      </div>
    );
  }
  if (detail.isLoading) return <Spinner />;
  if (!detail.data?.metrics) return null;

  const m = detail.data.metrics;
  const sharpe = m.sharpe;
  const lowSharpe = sharpe != null && sharpe < MIN_SHARPE_HINT;

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">{v.title}</h3>
        <button
          type="button"
          className="btn text-sm"
          disabled={aiSummary.isPending}
          onClick={() => aiSummary.mutate()}
        >
          {aiSummary.isPending ? ai.loading : ai.backtestBtn}
        </button>
      </div>
      <p className="mb-4 text-sm text-slate-500">{v.subtitle}</p>

      {lowSharpe && (
        <p className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
          {v.lowSharpeWarning}
        </p>
      )}

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label={v.sharpe} value={fmtNum(sharpe)} highlight={lowSharpe} />
        <Metric label={v.annualReturn} value={fmtPct(m.annual_return)} />
        <Metric label={v.maxDrawdown} value={fmtPct(m.max_drawdown)} />
        <Metric label={v.winRate} value={fmtPct(m.win_rate)} />
      </div>

      {insight && (
        <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50/50 p-4 text-sm text-slate-700 dark:border-brand-900 dark:bg-brand-950/30 dark:text-slate-200">
          <p className="mb-2 font-medium text-brand-700 dark:text-brand-300">{ai.backtestTitle}</p>
          <div className="whitespace-pre-wrap">{insight}</div>
        </div>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border px-3 py-2 ${
        highlight
          ? "border-rose-200 bg-rose-50/60 dark:border-rose-900 dark:bg-rose-950/30"
          : "border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900/40"
      }`}
    >
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

function fmtNum(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toFixed(2);
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

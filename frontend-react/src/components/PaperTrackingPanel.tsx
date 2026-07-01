import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getPaperHistory,
  refreshPaperSnapshot,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { Spinner } from "./ui";

export default function PaperTrackingPanel({
  factorId,
  enabled,
}: {
  factorId: string | null;
  enabled: boolean;
}) {
  const notify = useUi((s) => s.notify);
  const pt = useLocale((s) => s.dict.paperTracking);
  const c = useLocale((s) => s.dict.common);
  const qc = useQueryClient();

  const history = useQuery({
    queryKey: ["paper-history", factorId],
    queryFn: () => getPaperHistory(factorId!),
    enabled: Boolean(factorId && enabled),
  });

  const refresh = useMutation({
    mutationFn: () => refreshPaperSnapshot(factorId!),
    onSuccess: () => {
      notify(pt.refreshed, "success");
      void qc.invalidateQueries({ queryKey: ["paper-history", factorId] });
    },
    onError: (e) => notify(apiErrorMessage(e, pt.refreshFail), "error"),
  });

  if (!factorId || !enabled) {
    return (
      <div className="card text-sm text-slate-500">
        <h3 className="mb-2 font-semibold text-slate-800">{pt.title}</h3>
        <p>{pt.needValidation}</p>
      </div>
    );
  }

  if (history.isLoading) return <Spinner />;

  const snapshots = history.data?.snapshots ?? [];
  const preview = history.data?.latest_preview;
  const decay = history.data?.decay;
  const navSeries = snapshots.map((s) => s.nav_end);
  const latestNav = navSeries.length ? navSeries[navSeries.length - 1] : preview?.nav_end;

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800">{pt.title}</h3>
          <p className="text-xs text-slate-500">{pt.subtitle}</p>
        </div>
        <button
          className="btn-secondary text-sm"
          disabled={refresh.isPending}
          onClick={() => refresh.mutate()}
        >
          {refresh.isPending ? c.starting : pt.refresh}
        </button>
      </div>

      {decay && decay.status !== "ok" && (
        <div
          className={`mb-4 rounded-lg border px-3 py-2 text-sm ${
            decay.status === "alert"
              ? "border-rose-200 bg-rose-50 text-rose-800"
              : "border-amber-200 bg-amber-50 text-amber-800"
          }`}
        >
          <p className="font-medium">
            {decay.status === "alert" ? pt.decayAlert : pt.decayWatch}
          </p>
          {decay.reasons?.length > 0 && (
            <ul className="mt-1 list-inside list-disc text-xs opacity-90">
              {decay.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {preview && (
        <div className="mb-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
          <Metric label={pt.nav} value={latestNav?.toFixed(4) ?? "—"} />
          <Metric
            label={pt.sharpe}
            value={formatMetric(preview.metrics?.sharpe ?? preview.metrics?.sharpe_ratio)}
          />
          <Metric
            label={pt.maxDd}
            value={formatMetric(preview.metrics?.max_drawdown, true)}
          />
          <Metric label={pt.symbol} value={preview.symbol} />
        </div>
      )}

      {navSeries.length > 1 ? (
        <NavSparkline values={navSeries} />
      ) : (
        <p className="text-sm text-slate-400">{pt.historyHint}</p>
      )}

      {snapshots.length > 0 && (
        <p className="mt-3 text-xs text-slate-400">
          {pt.lastSnapshot}: {snapshots[snapshots.length - 1].as_of_date}
        </p>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="font-medium text-slate-800 dark:text-slate-100">{value}</div>
    </div>
  );
}

function formatMetric(v: unknown, pct = false): string {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return "—";
  return pct ? `${(n * 100).toFixed(1)}%` : n.toFixed(3);
}

function NavSparkline({ values }: { values: number[] }) {
  const w = 320;
  const h = 72;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = (i / Math.max(values.length - 1, 1)) * w;
      const y = h - ((v - min) / span) * (h - 8) - 4;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-20 w-full text-brand-600">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        points={pts}
      />
    </svg>
  );
}

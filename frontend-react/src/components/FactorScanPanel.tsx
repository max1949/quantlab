import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  applyFactorScan,
  compareFactorScans,
  createBacktest,
  createValidation,
  getEntitlements,
  getFactorTemplates,
  listFactorScans,
  reviewFactorScan,
  runFactorScan,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import type { FactorScan, FactorScanCompare } from "../api/types";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { Spinner } from "./ui";

type Props = {
  projectId: string;
  symbol: string;
  timeframe: string;
};

export default function FactorScanPanel({ projectId, symbol, timeframe }: Props) {
  const s = useLocale((x) => x.dict.factorScan);
  const ai = useLocale((x) => x.dict.aiReview);
  const lk = useLocale((x) => x.dict.locked);
  const notify = useUi((x) => x.notify);
  const qc = useQueryClient();
  const ent = useQuery({ queryKey: ["entitlements"], queryFn: getEntitlements });
  const templates = useQuery({ queryKey: ["factor-templates"], queryFn: getFactorTemplates });
  const history = useQuery({
    queryKey: ["factor-scans", projectId],
    queryFn: () => listFactorScans(projectId),
  });
  const scanFeat = ent.data?.features.find((f) => f.key === "factor_param_scan");

  const [templateType, setTemplateType] = useState("momentum");
  const [lastScan, setLastScan] = useState<FactorScan | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [compareResult, setCompareResult] = useState<FactorScanCompare | null>(null);
  const [aiInsight, setAiInsight] = useState<string | null>(null);

  const activeScan = lastScan;

  const scan = useMutation({
    mutationFn: () =>
      runFactorScan({
        symbol,
        template_type: templateType,
        timeframe,
        project_id: projectId,
        steps: 8,
      }),
    onSuccess: (data) => {
      setLastScan(data);
      setCompareResult(null);
      setAiInsight(null);
      notify(s.done, "success");
      if (data.academy_rewards?.length) {
        notify(s.academyXp(data.academy_rewards[0].awarded_xp), "success");
      }
      void qc.invalidateQueries({ queryKey: ["factor-scans", projectId] });
    },
    onError: (e) => notify(apiErrorMessage(e, s.fail), "error"),
  });

  const apply = useMutation({
    mutationFn: (rank: number) => applyFactorScan(activeScan!.id, { rank }),
    onSuccess: () => {
      notify(s.applied, "success");
      void qc.invalidateQueries({ queryKey: ["factors"] });
      void qc.invalidateQueries({ queryKey: ["graph", projectId] });
      void qc.invalidateQueries({ queryKey: ["factor-scans", projectId] });
    },
    onError: (e) => notify(apiErrorMessage(e, s.applyFail), "error"),
  });

  const applyAndValidate = useMutation({
    mutationFn: async (rank: number) => {
      const factor = await applyFactorScan(activeScan!.id, { rank });
      const bt = await createBacktest({ factor_id: factor.id, symbol, timeframe });
      const validation = await createValidation({ factor_id: factor.id, symbol, timeframe });
      return { factor, bt, validation };
    },
    onSuccess: () => {
      notify(s.validateStarted, "success");
      void qc.invalidateQueries({ queryKey: ["factors"] });
      void qc.invalidateQueries({ queryKey: ["backtests"] });
      void qc.invalidateQueries({ queryKey: ["validations"] });
      void qc.invalidateQueries({ queryKey: ["graph", projectId] });
      void qc.invalidateQueries({ queryKey: ["factor-scans", projectId] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
    },
    onError: (e) => notify(apiErrorMessage(e, s.validateFail), "error"),
  });

  const compare = useMutation({
    mutationFn: () => compareFactorScans(selectedIds[0], selectedIds[1]),
    onSuccess: (data) => {
      setCompareResult(data);
      notify(s.compareDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, s.compareFail), "error"),
  });

  const aiReview = useMutation({
    mutationFn: () => reviewFactorScan(activeScan!.id),
    onSuccess: (res) => {
      setAiInsight(res.content);
      notify(ai.done, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, ai.fail), "error"),
  });

  const historyRows = useMemo(
    () => history.data ?? [],
    [history.data],
  );

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
    setCompareResult(null);
  }

  function loadHistory(row: FactorScan) {
    setLastScan(row);
    setAiInsight(null);
    setCompareResult(null);
  }

  if (!scanFeat?.allowed) {
    return (
      <div className="card border-dashed border-slate-200 dark:border-slate-700">
        <p className="font-medium text-slate-700 dark:text-slate-200">{s.title}</p>
        <p className="mt-1 text-sm text-slate-500">{s.lockedHint}</p>
        <Link to="/pricing" className="mt-2 inline-block text-sm text-brand-600 hover:underline">
          {lk.unlock}
        </Link>
      </div>
    );
  }

  return (
    <div className="card border-brand-100 bg-brand-50/30 dark:border-brand-900 dark:bg-brand-950/20">
      <h3 className="font-semibold text-slate-800 dark:text-slate-100">{s.title}</h3>
      <p className="mt-1 text-sm text-slate-500">{s.subtitle}</p>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="label">{s.template}</label>
          <select
            className="input"
            value={templateType}
            onChange={(e) => setTemplateType(e.target.value)}
          >
            {(templates.data ?? [])
              .filter((t) => t.allowed !== false)
              .map((t) => (
                <option key={t.code} value={t.code}>
                  {t.label}
                </option>
              ))}
          </select>
        </div>
        <button
          type="button"
          className="btn-primary"
          disabled={!symbol || scan.isPending}
          onClick={() => scan.mutate()}
        >
          {scan.isPending ? s.running : s.run}
        </button>
      </div>

      {scan.isPending && <Spinner />}

      {historyRows.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{s.history}</p>
            <button
              type="button"
              className="btn text-xs"
              disabled={selectedIds.length !== 2 || compare.isPending}
              onClick={() => compare.mutate()}
            >
              {compare.isPending ? s.comparing : s.compare}
            </button>
          </div>
          <ul className="space-y-1 text-sm">
            {historyRows.slice(0, 8).map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center gap-2 rounded border border-slate-100 px-2 py-1 dark:border-slate-800"
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(row.id)}
                  onChange={() => toggleSelect(row.id)}
                  aria-label={s.selectForCompare}
                />
                <button
                  type="button"
                  className="text-left text-brand-700 hover:underline dark:text-brand-300"
                  onClick={() => loadHistory(row)}
                >
                  {row.template_type} · {row.timeframe} · {row.best_score?.toFixed(2) ?? "—"}
                </button>
                <span className="text-xs text-slate-400">
                  {new Date(row.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {compareResult && (
        <div className="mt-3 rounded-lg border border-violet-200 bg-violet-50/60 px-3 py-2 text-sm text-violet-900 dark:border-violet-900 dark:bg-violet-950/30 dark:text-violet-100">
          <p className="font-medium">{s.compareTitle}</p>
          <p className="mt-1">{compareResult.summary}</p>
          <p className="mt-1 text-xs opacity-80">
            Δ score {fmtDelta(compareResult.delta.score)} · Δ OOS {fmtDelta(compareResult.delta.oos_sharpe)} · Δ IC{" "}
            {fmtDelta(compareResult.delta.ic_mean)}
          </p>
        </div>
      )}

      {activeScan && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
              {activeScan.coach_summary}
            </div>
            <button
              type="button"
              className="btn text-sm"
              disabled={aiReview.isPending}
              onClick={() => aiReview.mutate()}
            >
              {aiReview.isPending ? ai.loading : ai.scanBtn}
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs text-slate-400">
                  <th className="py-2 pr-2">#</th>
                  <th className="py-2 pr-2">{s.colParams}</th>
                  <th className="py-2 pr-2">{s.colScore}</th>
                  <th className="py-2 pr-2">{s.colSharpe}</th>
                  <th className="py-2 pr-2">{s.colOos}</th>
                  <th className="py-2 pr-2">{s.colIc}</th>
                  <th className="py-2 pr-2">{s.colTurnover}</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {activeScan.results.slice(0, 12).map((row) => (
                  <tr key={row.rank} className="border-b border-slate-100 dark:border-slate-800">
                    <td className="py-2 pr-2">{row.rank}</td>
                    <td className="py-2 pr-2 font-mono text-xs">{row.label}</td>
                    <td className="py-2 pr-2 font-medium">{row.score ?? "—"}</td>
                    <td className="py-2 pr-2">{fmt(row.sharpe)}</td>
                    <td className="py-2 pr-2">{fmt(row.oos_sharpe)}</td>
                    <td className="py-2 pr-2">{fmt(row.ic_mean)}</td>
                    <td className="py-2 pr-2">{fmt(row.turnover)}</td>
                    <td className="py-2">
                      <div className="flex flex-wrap gap-1">
                        <button
                          type="button"
                          className="btn text-xs"
                          disabled={apply.isPending || applyAndValidate.isPending}
                          onClick={() => apply.mutate(row.rank)}
                        >
                          {s.apply}
                        </button>
                        <button
                          type="button"
                          className="btn-primary px-2 py-1 text-xs"
                          disabled={apply.isPending || applyAndValidate.isPending}
                          onClick={() => applyAndValidate.mutate(row.rank)}
                        >
                          {applyAndValidate.isPending ? s.validating : s.applyAndValidate}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {aiInsight && (
            <div className="rounded-lg border border-brand-200 bg-brand-50/50 p-4 text-sm text-slate-700 dark:border-brand-900 dark:bg-brand-950/30 dark:text-slate-200">
              <p className="mb-2 font-medium text-brand-700 dark:text-brand-300">{ai.scanTitle}</p>
              <div className="whitespace-pre-wrap">{aiInsight}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function fmt(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toFixed(2);
}

function fmtDelta(v: number | null | undefined): string {
  if (v == null) return "—";
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}`;
}

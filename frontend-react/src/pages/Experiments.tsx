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
  reviewFactorScansBatch,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import type { FactorScan, FactorScanCompare } from "../api/types";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Experiments() {
  const e = useLocale((s) => s.dict.experiments);
  const fs = useLocale((s) => s.dict.factorScan);
  const ai = useLocale((s) => s.dict.aiReview);
  const common = useLocale((s) => s.dict.common);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();

  const [symbolFilter, setSymbolFilter] = useState("");
  const [templateFilter, setTemplateFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareResult, setCompareResult] = useState<FactorScanCompare | null>(null);
  const [aiInsight, setAiInsight] = useState<string | null>(null);

  const ent = useQuery({ queryKey: ["entitlements"], queryFn: getEntitlements });
  const templates = useQuery({ queryKey: ["factor-templates"], queryFn: getFactorTemplates });
  const scanFeat = ent.data?.features.find((f) => f.key === "factor_param_scan");
  const allowed = scanFeat?.allowed ?? false;

  const scans = useQuery({
    queryKey: ["factor-scans", "all", symbolFilter, templateFilter],
    queryFn: () =>
      listFactorScans({
        symbol: symbolFilter.trim() || undefined,
        templateType: templateFilter || undefined,
        limit: 50,
      }),
    enabled: allowed,
  });

  const selected = useMemo(
    () => scans.data?.find((s) => s.id === selectedId) ?? null,
    [scans.data, selectedId],
  );

  const compare = useMutation({
    mutationFn: () => compareFactorScans(compareIds[0], compareIds[1]),
    onSuccess: (data) => {
      setCompareResult(data);
      notify(fs.compareDone, "success");
    },
    onError: (err) => notify(apiErrorMessage(err, fs.compareFail), "error"),
  });

  const aiBatch = useMutation({
    mutationFn: () => reviewFactorScansBatch(compareIds),
    onSuccess: (res) => {
      setAiInsight(res.content);
      notify(ai.done, "success");
    },
    onError: (err) => notify(apiErrorMessage(err, ai.fail), "error"),
  });

  const apply = useMutation({
    mutationFn: (rank: number) => applyFactorScan(selected!.id, { rank }),
    onSuccess: () => {
      notify(fs.applied, "success");
      void qc.invalidateQueries({ queryKey: ["factor-scans"] });
      void qc.invalidateQueries({ queryKey: ["factors"] });
    },
    onError: (err) => notify(apiErrorMessage(err, fs.applyFail), "error"),
  });

  const applyAndValidate = useMutation({
    mutationFn: async (rank: number) => {
      const factor = await applyFactorScan(selected!.id, { rank });
      await createBacktest({
        factor_id: factor.id,
        symbol: selected!.symbol,
        timeframe: selected!.timeframe,
      });
      await createValidation({
        factor_id: factor.id,
        symbol: selected!.symbol,
        timeframe: selected!.timeframe,
      });
      return factor;
    },
    onSuccess: () => {
      notify(fs.validateStarted, "success");
      void qc.invalidateQueries({ queryKey: ["factor-scans"] });
      void qc.invalidateQueries({ queryKey: ["factors"] });
      void qc.invalidateQueries({ queryKey: ["backtests"] });
      void qc.invalidateQueries({ queryKey: ["validations"] });
    },
    onError: (err) => notify(apiErrorMessage(err, fs.validateFail), "error"),
  });

  const aiReview = useMutation({
    mutationFn: () => reviewFactorScan(selected!.id),
    onSuccess: (res) => {
      setAiInsight(res.content);
      notify(ai.done, "success");
    },
    onError: (err) => notify(apiErrorMessage(err, ai.fail), "error"),
  });

  function toggleCompare(id: string) {
    setCompareResult(null);
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 5) return [...prev.slice(1), id];
      return [...prev, id];
    });
  }

  if (ent.isLoading) return <Spinner />;

  if (!allowed) {
    return (
      <div>
        <PageTitle title={e.title} subtitle={e.subtitle} />
        <div className="card border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
          <p className="text-sm text-amber-900 dark:text-amber-100">{e.lockedHint}</p>
          <Link to="/pricing" className="btn-primary mt-3 inline-block">
            {common.upgrade}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageTitle title={e.title} subtitle={e.subtitle} />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="mb-1 block text-xs text-slate-500">{e.filterSymbol}</span>
          <input
            className="input w-28"
            value={symbolFilter}
            onChange={(ev) => setSymbolFilter(ev.target.value.toUpperCase())}
            placeholder="RB"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-slate-500">{e.filterTemplate}</span>
          <select
            className="input"
            value={templateFilter}
            onChange={(ev) => setTemplateFilter(ev.target.value)}
          >
            <option value="">{e.filterAll}</option>
            {(templates.data ?? []).map((t) => (
              <option key={t.code} value={t.code}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        {compareIds.length === 2 && (
          <button
            type="button"
            className="btn-primary"
            disabled={compare.isPending}
            onClick={() => compare.mutate()}
          >
            {compare.isPending ? fs.comparing : e.compareSelected}
          </button>
        )}
        {compareIds.length >= 2 && compareIds.length <= 5 && (
          <button
            type="button"
            className="btn"
            disabled={aiBatch.isPending}
            onClick={() => aiBatch.mutate()}
          >
            {aiBatch.isPending ? ai.loading : e.aiBatchReview}
          </button>
        )}
      </div>

      {scans.isLoading ? (
        <Spinner />
      ) : scans.isError ? (
        <ErrorBox message={apiErrorMessage(scans.error)} />
      ) : scans.data && scans.data.length > 0 ? (
        <div className="space-y-4">
          <p className="text-xs text-slate-500">{e.selectHint}</p>
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b bg-slate-50/80 text-xs text-slate-500 dark:bg-slate-900/60">
                  <th className="px-3 py-2" />
                  <th className="px-3 py-2">{e.colDate}</th>
                  <th className="px-3 py-2">{fs.colParams}</th>
                  <th className="px-3 py-2">{fs.template}</th>
                  <th className="px-3 py-2">{e.filterSymbol}</th>
                  <th className="px-3 py-2">TF</th>
                  <th className="px-3 py-2">{fs.colScore}</th>
                  <th className="px-3 py-2">{e.colProject}</th>
                  <th className="px-3 py-2">{e.colApplied}</th>
                </tr>
              </thead>
              <tbody>
                {scans.data.map((row) => (
                  <tr
                    key={row.id}
                    className={`cursor-pointer border-b border-slate-100 dark:border-slate-800 ${
                      selectedId === row.id ? "bg-brand-50/60 dark:bg-brand-950/30" : "hover:bg-slate-50 dark:hover:bg-slate-900/40"
                    }`}
                    onClick={() => {
                      setSelectedId(row.id);
                      setAiInsight(null);
                      setCompareResult(null);
                    }}
                  >
                    <td className="px-3 py-2" onClick={(ev) => ev.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={compareIds.includes(row.id)}
                        onChange={() => toggleCompare(row.id)}
                        aria-label={fs.selectForCompare}
                      />
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-slate-500">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {row.results[0]?.label ?? "—"}
                    </td>
                    <td className="px-3 py-2">{formatScanType(row.template_type)}</td>
                    <td className="px-3 py-2">{row.symbol}</td>
                    <td className="px-3 py-2">{row.timeframe}</td>
                    <td className="px-3 py-2 font-medium">{fmt(row.best_score)}</td>
                    <td className="px-3 py-2">
                      {row.project_id ? (
                        <Link
                          to={`/projects/${row.project_id}#factor-scan`}
                          className="text-brand-700 hover:underline dark:text-brand-300"
                          onClick={(ev) => ev.stopPropagation()}
                        >
                          {row.project_title ?? e.openProject}
                        </Link>
                      ) : (
                        <span className="text-slate-400">{e.noProject}</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {row.applied_factor_id ? e.appliedYes : e.appliedNo}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

      {compareResult && (
        <div className="rounded-lg border border-violet-200 bg-violet-50/60 px-3 py-2 text-sm text-violet-900 dark:border-violet-900 dark:bg-violet-950/30 dark:text-violet-100">
          <p className="font-medium">{fs.compareTitle}</p>
          <p className="mt-1">{compareResult.summary}</p>
        </div>
      )}

      {aiInsight && compareIds.length >= 2 && !selected && (
        <div className="rounded-lg border border-brand-200 bg-brand-50/50 p-4 text-sm text-slate-700 dark:border-brand-900 dark:bg-brand-950/30 dark:text-slate-200">
          <p className="mb-2 font-medium text-brand-700 dark:text-brand-300">{ai.scanBatchTitle}</p>
          <div className="whitespace-pre-wrap">{aiInsight}</div>
        </div>
      )}

          {selected && (
            <ScanDetail
              scan={selected}
              fs={fs}
              e={e}
              ai={ai}
              aiInsight={aiInsight}
              onAiReview={() => aiReview.mutate()}
              aiPending={aiReview.isPending}
              onApply={(rank) => apply.mutate(rank)}
              onApplyValidate={(rank) => applyAndValidate.mutate(rank)}
              actionsPending={apply.isPending || applyAndValidate.isPending}
            />
          )}
        </div>
      ) : (
        <EmptyState
          title={e.emptyTitle}
          hint={e.emptyHint}
          action={
            <Link to="/projects" className="btn-primary mt-2">
              {e.goProjects}
            </Link>
          }
        />
      )}
    </div>
  );
}

import type { Dictionary } from "../i18n/dictionaries";

function ScanDetail({
  scan,
  fs,
  e,
  ai,
  aiInsight,
  onAiReview,
  aiPending,
  onApply,
  onApplyValidate,
  actionsPending,
}: {
  scan: FactorScan;
  fs: Dictionary["factorScan"];
  e: Dictionary["experiments"];
  ai: Dictionary["aiReview"];
  aiInsight: string | null;
  onAiReview: () => void;
  aiPending: boolean;
  onApply: (rank: number) => void;
  onApplyValidate: (rank: number) => void;
  actionsPending: boolean;
}) {
  const top = scan.results[0];

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{e.detailTitle}</h3>
          <p className="text-xs text-slate-500">
            {formatScanType(scan.template_type)} · {scan.symbol} · {scan.timeframe}
          </p>
        </div>
        <button type="button" className="btn text-sm" disabled={aiPending} onClick={onAiReview}>
          {aiPending ? ai.loading : ai.scanBtn}
        </button>
      </div>

      <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        {scan.coach_summary}
      </div>

      {top?.publish_hints && top.publish_hints.length > 0 && (
        <div
          className={`mb-3 rounded-lg border px-3 py-2 text-sm ${
            top.publish_promising
              ? "border-emerald-300 bg-emerald-50/70 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100"
              : "border-amber-300 bg-amber-50/70 text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
          }`}
        >
          <p className="font-medium">{fs.publishHintTitle}</p>
          <ul className="mt-1 list-inside list-disc text-xs opacity-90">
            {top.publish_hints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-xs text-slate-400">
              <th className="py-2 pr-2">#</th>
              <th className="py-2 pr-2">{fs.colParams}</th>
              <th className="py-2 pr-2">{fs.colScore}</th>
              <th className="py-2 pr-2">{fs.colSharpe}</th>
              <th className="py-2 pr-2">{fs.colOos}</th>
              <th className="py-2 pr-2">{fs.colIc}</th>
              <th className="py-2 pr-2">{fs.colTurnover}</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {scan.results.slice(0, 12).map((row) => (
              <tr key={row.rank} className="border-b border-slate-100 dark:border-slate-800">
                <td className="py-2 pr-2">{row.rank}</td>
                <td className="py-2 pr-2 font-mono text-xs">{row.label}</td>
                <td className="py-2 pr-2 font-medium">{fmt(row.score)}</td>
                <td className="py-2 pr-2">{fmt(row.sharpe)}</td>
                <td className="py-2 pr-2">{fmt(row.oos_sharpe)}</td>
                <td className="py-2 pr-2">{fmt(row.ic_mean)}</td>
                <td className="py-2 pr-2">{fmt(row.turnover)}</td>
                <td className="py-2">
                  <div className="flex flex-wrap gap-1">
                    <button
                      type="button"
                      className="btn text-xs"
                      disabled={actionsPending}
                      onClick={() => onApply(row.rank)}
                    >
                      {fs.apply}
                    </button>
                    <button
                      type="button"
                      className="btn-primary px-2 py-1 text-xs"
                      disabled={actionsPending}
                      onClick={() => onApplyValidate(row.rank)}
                    >
                      {actionsPending ? fs.validating : fs.applyAndValidate}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {aiInsight && (
        <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50/50 p-4 text-sm text-slate-700 dark:border-brand-900 dark:bg-brand-950/30 dark:text-slate-200">
          <p className="mb-2 font-medium text-brand-700 dark:text-brand-300">{ai.scanTitle}</p>
          <div className="whitespace-pre-wrap">{aiInsight}</div>
        </div>
      )}
    </div>
  );
}

function fmt(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toFixed(2);
}

function formatScanType(templateType: string): string {
  if (templateType.startsWith("stack:")) return "stack";
  return templateType;
}

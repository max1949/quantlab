import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createBacktest,
  createValidation,
  generateReport,
  getGraph,
  getProject,
  getProjectQuality,
  listFactors,
  publishProject,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import FactorLab from "../components/FactorLab";
import AdvancedAnalysis from "../components/AdvancedAnalysis";
import L3ResearchTools from "../components/L3ResearchTools";
import L4PortfolioTools from "../components/L4PortfolioTools";
import type { Graph } from "../api/types";

type StepKey = "factor" | "backtest" | "validation" | "report" | "publish";

export default function ProjectDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const p = useLocale((s) => s.dict.projectDetail);
  const lk = useLocale((s) => s.dict.locked);

  const project = useQuery({ queryKey: ["project", id], queryFn: () => getProject(id) });
  const factors = useQuery({ queryKey: ["factors"], queryFn: listFactors });
  const graph = useQuery({ queryKey: ["graph", id], queryFn: () => getGraph(id) });
  const quality = useQuery({
    queryKey: ["project-quality", id],
    queryFn: () => getProjectQuality(id),
    enabled: Boolean(id),
  });

  const projectFactors = useMemo(
    () => (factors.data ?? []).filter((f) => f.project_id === id),
    [factors.data, id],
  );
  const [selectedFactorId, setSelectedFactorId] = useState<string>("");
  const projectFactor =
    projectFactors.find((f) => f.id === selectedFactorId) ??
    projectFactors[0] ??
    null;

  const symbol = project.data?.symbol || "";

  const done = useMemo(() => computeDone(graph.data, project.data?.status), [
    graph.data,
    project.data?.status,
  ]);

  const [busy, setBusy] = useState<StepKey | null>(null);

  function refreshAll() {
    void qc.invalidateQueries({ queryKey: ["graph", id] });
    void qc.invalidateQueries({ queryKey: ["project", id] });
    void qc.invalidateQueries({ queryKey: ["project-quality", id] });
    void qc.invalidateQueries({ queryKey: ["projects"] });
  }

  const runBacktest = useMutation({
    mutationFn: () =>
      createBacktest({ factor_id: projectFactor!.id, symbol }),
    onMutate: () => setBusy("backtest"),
    onSuccess: (bt) => {
      void trackEvent("backtest_run", { project: id, status: bt.status });
      notify(p.backtestDone(bt.status), "success");
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, p.backtestFail), "error"),
    onSettled: () => setBusy(null),
  });

  const runValidation = useMutation({
    mutationFn: () =>
      createValidation({ factor_id: projectFactor!.id, symbol }),
    onMutate: () => setBusy("validation"),
    onSuccess: (v) => {
      void trackEvent("validation_run", { project: id, status: v.status });
      notify(p.validationDone(v.status), "success");
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, p.validationFail), "error"),
    onSettled: () => setBusy(null),
  });

  const genReport = useMutation({
    mutationFn: () => generateReport({ project_id: id }),
    onMutate: () => setBusy("report"),
    onSuccess: (r) => {
      void trackEvent("report_generated", { project: id });
      notify(p.reportDone, "success");
      refreshAll();
      navigate(`/reports/${r.id}`);
    },
    onError: (e) => notify(apiErrorMessage(e, p.reportFail), "error"),
    onSettled: () => setBusy(null),
  });

  const publish = useMutation({
    mutationFn: () => publishProject(id),
    onMutate: () => setBusy("publish"),
    onSuccess: () => {
      void trackEvent("project_published", { project: id });
      notify(p.publishDone, "success");
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, p.publishFail), "error"),
    onSettled: () => setBusy(null),
  });

  if (project.isLoading) return <Spinner />;
  if (project.isError)
    return <ErrorBox message={apiErrorMessage(project.error, p.notFound)} />;

  const proj = project.data!;

  const stepOrder: StepKey[] = ["factor", "backtest", "validation", "report", "publish"];
  const finishedCount = stepOrder.filter((k) => done[k]).length;
  const nextKey = stepOrder.find((k) => !done[k]) ?? null;

  const steps: {
    key: StepKey;
    title: string;
    desc: string;
    cta: string;
    run?: () => void;
    pending: boolean;
    disabled: boolean;
  }[] = [
    {
      key: "factor",
      title: p.stepFactor,
      desc: projectFactor ? p.stepFactorReady(projectFactor.name) : p.stepFactorEmpty,
      cta: p.stepFactorDone,
      pending: false,
      disabled: true,
    },
    {
      key: "backtest",
      title: p.stepBacktest,
      desc: p.stepBacktestDesc,
      cta: p.runBacktest,
      run: () => runBacktest.mutate(),
      pending: busy === "backtest",
      disabled: !projectFactor || done.backtest,
    },
    {
      key: "validation",
      title: p.stepValidation,
      desc: p.stepValidationDesc,
      cta: p.runValidation,
      run: () => runValidation.mutate(),
      pending: busy === "validation",
      disabled: !projectFactor || !done.backtest || done.validation,
    },
    {
      key: "report",
      title: p.stepReport,
      desc: p.stepReportDesc,
      cta: p.genReport,
      run: () => genReport.mutate(),
      pending: busy === "report",
      disabled: !done.backtest,
    },
    {
      key: "publish",
      title: p.stepPublish,
      desc: p.stepPublishDesc,
      cta: proj.status === "published" ? p.published : p.publishProject,
      run: () => publish.mutate(),
      pending: busy === "publish",
      disabled: !done.report || proj.status === "published",
    },
  ];

  return (
    <div>
      <PageTitle title={proj.title} subtitle={proj.question || proj.description} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="badge">
          {p.status} {proj.status}
        </span>
        {proj.symbol && (
          <span className="badge">
            {p.symbol} {proj.symbol}
          </span>
        )}
        {proj.tags?.map((t) => (
          <span key={t} className="badge">
            #{t}
          </span>
        ))}
      </div>

      {projectFactors.length > 1 && (
        <div className="mb-4 flex items-center gap-2 text-sm">
          <span className="text-slate-500">{p.factorForRun}</span>
          <select
            className="input max-w-xs"
            value={projectFactor?.id ?? ""}
            onChange={(e) => setSelectedFactorId(e.target.value)}
          >
            {projectFactors.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="mb-6 card">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-medium text-slate-700 dark:text-slate-200">{p.progressLabel}</span>
          <span className="text-slate-500">{p.progressSteps(finishedCount, stepOrder.length)}</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${(finishedCount / stepOrder.length) * 100}%` }}
          />
        </div>
      </div>

      {quality.data && (
        <div
          className={`mb-6 card border ${
            quality.data.passed
              ? "border-emerald-200 bg-emerald-50/40 dark:border-emerald-900 dark:bg-emerald-950/30"
              : "border-amber-200 bg-amber-50/40 dark:border-amber-900 dark:bg-amber-950/20"
          }`}
        >
          <p className="font-semibold text-slate-800 dark:text-slate-100">
            {quality.data.passed ? p.qualityPass : p.qualityFail}
          </p>
          {!quality.data.passed && quality.data.reasons.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-sm text-slate-600 dark:text-slate-300">
              {quality.data.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3">
          {steps.map((s) => {
            const finished = done[s.key as keyof typeof done];
            const isNext = s.key === nextKey;
            return (
              <div
                key={s.key}
                className={`card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${
                  finished ? "border-emerald-200 bg-emerald-50/40" : ""
                } ${isNext ? "ring-2 ring-brand-400 ring-offset-2 dark:ring-offset-slate-950" : ""}`}
              >
                <div className="min-w-0">
                  {isNext && (
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-600">
                      {p.nextUp}
                    </p>
                  )}
                  <p className="font-semibold text-slate-800">
                    {finished && "✅ "}
                    {s.title}
                  </p>
                  <p className="text-sm text-slate-500">{s.desc}</p>
                </div>
                {s.run && (
                  <button
                    className="btn-primary w-full shrink-0 whitespace-nowrap sm:w-auto"
                    disabled={s.disabled || s.pending}
                    onClick={s.run}
                  >
                    {s.pending ? lk.running : s.cta}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <div className="card">
          <h3 className="mb-3 font-semibold">{p.graphTitle}</h3>
          {graph.isLoading ? (
            <Spinner />
          ) : graph.data && graph.data.nodes.length > 0 ? (
            <GraphView graph={graph.data} />
          ) : (
            <p className="py-6 text-center text-sm text-slate-400">{p.graphEmpty}</p>
          )}
        </div>
      </div>

      <div className="mt-4">
        <FactorLab projectId={id} />
      </div>

      <div className="mt-4">
        <AdvancedAnalysis
          projectId={id}
          factorId={projectFactor?.id ?? null}
          symbol={symbol}
        />
      </div>

      <div className="mt-4">
        <L3ResearchTools
          projectId={id}
          factors={projectFactors}
          selectedFactorId={projectFactor?.id ?? null}
          symbol={symbol}
        />
      </div>

      <div className="mt-4">
        <L4PortfolioTools projectId={id} />
      </div>

      <p className="mt-6 text-sm text-slate-400">
        <Link to="/projects" className="text-brand-600">
          {p.backToProjects}
        </Link>
      </p>
    </div>
  );
}

const KIND_STYLE: Record<string, string> = {
  hypothesis: "bg-purple-100 text-purple-700",
  experiment: "bg-brand-100 text-brand-700",
  validation: "bg-emerald-100 text-emerald-700",
  result: "bg-rose-100 text-rose-700",
};

function GraphView({ graph }: { graph: Graph }) {
  const ordered = [...graph.nodes].sort((a, b) => a.order - b.order);
  return (
    <ol className="relative space-y-3 border-l-2 border-slate-200 pl-4">
      {ordered.map((n) => (
        <li key={n.id} className="relative">
          <span className="absolute -left-[21px] top-1.5 h-3 w-3 rounded-full bg-brand-500 ring-4 ring-white" />
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              KIND_STYLE[n.kind] ?? "bg-slate-100 text-slate-600"
            }`}
          >
            {n.kind}
          </span>
          <p className="mt-0.5 text-sm font-medium text-slate-700">{n.label}</p>
        </li>
      ))}
    </ol>
  );
}

function computeDone(graph: Graph | undefined, status: string | undefined) {
  const refTypes = new Set(
    (graph?.nodes ?? []).map((n) => n.ref_type).filter(Boolean) as string[],
  );
  return {
    factor: refTypes.has("factor"),
    backtest: refTypes.has("backtest"),
    validation: refTypes.has("validation"),
    report: refTypes.has("report"),
    publish: status === "published",
  };
}

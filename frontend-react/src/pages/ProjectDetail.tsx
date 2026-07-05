import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createBacktest,
  createValidation,
  generateReport,
  getEntitlements,
  getGraph,
  getProject,
  getProjectQuality,
  listDatasets,
  listFactors,
  publishProject,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { academyRewardMessage } from "../lib/academy";
import { celebrateFirstReport } from "../lib/celebrateFirstReport";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import FactorLab from "../components/FactorLab";
import FactorScanPanel from "../components/FactorScanPanel";
import AdvancedAnalysis from "../components/AdvancedAnalysis";
import L3ResearchTools from "../components/L3ResearchTools";
import PaperTrackingPanel from "../components/PaperTrackingPanel";
import L4PortfolioTools from "../components/L4PortfolioTools";
import ValidationResultsPanel from "../components/ValidationResultsPanel";
import BacktestResultsPanel from "../components/BacktestResultsPanel";
import QualityCoach from "../components/QualityCoach";
import MasteryPathPanel from "../components/MasteryPathPanel";
import ProjectRegimePanel from "../components/ProjectRegimePanel";
import FailureCoachPanel from "../components/FailureCoachPanel";
import AttentionCoachPanel from "../components/AttentionCoachPanel";
import PublishFeedPreview from "../components/PublishFeedPreview";
import DataQualityBanner from "../components/DataQualityBanner";
import VolRegimeBanner from "../components/VolRegimeBanner";
import FirstProjectCoachPanel from "../components/FirstProjectCoachPanel";
import FirstBacktestCoachPanel from "../components/FirstBacktestCoachPanel";
import FirstValidationCoachPanel from "../components/FirstValidationCoachPanel";
import FactorCatalogPanel from "../components/FactorCatalogPanel";
import { FIRST_BACKTEST_WELCOME_KEY, FIRST_REPORT_WELCOME_KEY, FIRST_VALIDATION_WELCOME_KEY } from "../lib/onboardingFocus";
import type { Graph } from "../api/types";

type StepKey = "factor" | "backtest" | "validation" | "report" | "publish";

export default function ProjectDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const setUser = useAuth((s) => s.setUser);
  const p = useLocale((s) => s.dict.projectDetail);
  const d = useLocale((s) => s.dict.dashboard);
  const firstReportCoach = useLocale((s) => s.dict.firstReportCoach);
  const lk = useLocale((s) => s.dict.locked);

  const project = useQuery({ queryKey: ["project", id], queryFn: () => getProject(id) });
  const factors = useQuery({ queryKey: ["factors"], queryFn: listFactors });
  const graph = useQuery({ queryKey: ["graph", id], queryFn: () => getGraph(id) });
  const quality = useQuery({
    queryKey: ["project-quality", id],
    queryFn: () => getProjectQuality(id),
    enabled: Boolean(id),
  });
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
  const entitlements = useQuery({
    queryKey: ["entitlements"],
    queryFn: getEntitlements,
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

  const timeframeOptions = useMemo(() => {
    const allowed = entitlements.data?.market_data?.allowed_timeframes;
    if (!symbol || !datasets.data) return allowed?.length ? [...allowed] : ["1d"];
    const tfs = datasets.data.filter((d) => d.symbol === symbol).map((d) => d.timeframe);
    const unique = tfs.length ? Array.from(new Set(tfs)).sort() : ["1d"];
    if (!allowed?.length) return unique;
    return unique.filter((tf) => allowed.includes(tf));
  }, [datasets.data, symbol, entitlements.data]);

  const [timeframe, setTimeframe] = useState("1d");
  const activeTimeframe = timeframeOptions.includes(timeframe) ? timeframe : timeframeOptions[0];

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
      createBacktest({ factor_id: projectFactor!.id, symbol, timeframe: activeTimeframe }),
    onMutate: () => setBusy("backtest"),
    onSuccess: async (bt) => {
      void trackEvent("backtest_run", { project: id, status: bt.status });
      notify(p.backtestDone(bt.status), "success");
      if (bt.status === "success") {
        sessionStorage.setItem(FIRST_BACKTEST_WELCOME_KEY, id);
      }
      const msg = academyRewardMessage(bt.academy_rewards, d.academyXpEarned);
      if (msg) notify(msg, "success");
      void qc.invalidateQueries({ queryKey: ["backtests"] });
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      const me = await useAuth.getState().refreshMe();
      if (me) setUser(me);
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, p.backtestFail), "error"),
    onSettled: () => setBusy(null),
  });

  const runValidation = useMutation({
    mutationFn: () =>
      createValidation({ factor_id: projectFactor!.id, symbol, timeframe: activeTimeframe }),
    onMutate: () => setBusy("validation"),
    onSuccess: async (v) => {
      void trackEvent("validation_run", { project: id, status: v.status });
      notify(p.validationDone(v.status), "success");
      if (v.status === "success") {
        sessionStorage.setItem(FIRST_VALIDATION_WELCOME_KEY, id);
      }
      const msg = academyRewardMessage(v.academy_rewards, d.academyXpEarned);
      if (msg) notify(msg, "success");
      void qc.invalidateQueries({ queryKey: ["validations"] });
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      const me = await useAuth.getState().refreshMe();
      if (me) setUser(me);
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, p.validationFail), "error"),
    onSettled: () => setBusy(null),
  });

  const genReport = useMutation({
    mutationFn: () => generateReport({ project_id: id }),
    onMutate: () => setBusy("report"),
    onSuccess: async (r) => {
      void trackEvent("report_generated", { project: id });
      notify(p.reportDone, "success");
      const first = celebrateFirstReport(
        r,
        { celebrate: firstReportCoach.reportCelebrate, academyXpEarned: d.academyXpEarned },
        notify,
        { confetti: false },
      );
      sessionStorage.setItem(FIRST_REPORT_WELCOME_KEY, r.id);
      if (!first) {
        const msg = academyRewardMessage(r.academy_rewards, d.academyXpEarned);
        if (msg) notify(msg, "success");
      }
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      await qc.refetchQueries({ queryKey: ["research-journey"] });
      const me = await useAuth.getState().refreshMe();
      if (me) setUser(me);
      refreshAll();
      navigate(`/reports/${r.id}`);
    },
    onError: (e) => notify(apiErrorMessage(e, p.reportFail), "error"),
    onSettled: () => setBusy(null),
  });

  const publish = useMutation({
    mutationFn: () => publishProject(id),
    onMutate: () => setBusy("publish"),
    onSuccess: async (res) => {
      void trackEvent("project_published", { project: id });
      notify(p.publishDone, "success");
      const msg = academyRewardMessage(res.academy_rewards, d.academyXpEarned);
      if (msg) notify(msg, "success");
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      const me = await useAuth.getState().refreshMe();
      if (me) setUser(me);
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, p.publishFail), "error"),
    onSettled: () => setBusy(null),
  });

  if (project.isLoading) return <Spinner />;
  if (project.isError)
    return <ErrorBox message={apiErrorMessage(project.error, p.notFound)} />;

  function scrollToFactorLab() {
    document.getElementById("factor-lab")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToPaperExecution() {
    document.getElementById("paper-execution")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToPaperTracking() {
    document.getElementById("paper-tracking")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function handleMasteryAction(action: string) {
    if (action === "backtest" && projectFactor && !done.backtest) {
      runBacktest.mutate();
      return;
    }
    if (
      (action === "validate" || action === "validation") &&
      projectFactor &&
      done.backtest &&
      !done.validation
    ) {
      runValidation.mutate();
      return;
    }
    if (action === "graduate") {
      document.getElementById("mastery-quality")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    if (action === "paper") {
      scrollToPaperExecution();
      return;
    }
    if (action === "track") {
      scrollToPaperTracking();
      return;
    }
    if (action === "revalidate") {
      scrollToFactorLab();
      if (projectFactor && done.backtest) {
        setTimeout(() => runValidation.mutate(), 400);
      }
      return;
    }
    if (action === "share" || action === "publish") {
      if (quality.data?.passed && !done.publish) publish.mutate();
      else scrollToFactorLab();
      return;
    }
    if (action === "templates") {
      navigate(`/templates?symbol=${encodeURIComponent(symbol || "RB")}`);
      return;
    }
    scrollToFactorLab();
  }

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
      disabled: !done.backtest || !done.validation || done.report,
    },
    {
      key: "publish",
      title: p.stepPublish,
      desc: p.stepPublishDesc,
      cta: proj.status === "published" ? p.published : p.publishProject,
      run: () => publish.mutate(),
      pending: busy === "publish",
      disabled:
        !done.report ||
        proj.status === "published" ||
        (quality.data != null && !quality.data.passed),
    },
  ];

  const activeDataset = datasets.data?.find(
    (d) => d.symbol === symbol && d.timeframe === activeTimeframe,
  );
  const barCount = activeDataset?.effective_rows ?? activeDataset?.rows ?? null;
  const barsCapped =
    Boolean(activeDataset) &&
    activeDataset!.tier_cap != null &&
    activeDataset!.rows > (activeDataset!.effective_rows ?? activeDataset!.rows);

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

      <FirstProjectCoachPanel
        projectId={id}
        backtestDone={done.backtest}
        backtestPending={busy === "backtest"}
        onRunBacktest={() => runBacktest.mutate()}
      />

      <FirstBacktestCoachPanel
        projectId={id}
        backtestDone={done.backtest}
        validationDone={done.validation}
        validationPending={busy === "validation"}
        onRunValidation={() => runValidation.mutate()}
      />

      <FirstValidationCoachPanel
        projectId={id}
        validationDone={done.validation}
        reportDone={done.report}
        reportPending={busy === "report"}
        onGenerateReport={() => genReport.mutate()}
      />

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

      {entitlements.data?.market_data?.summary && (
        <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300">
          {p.dataPlanLabel}: {entitlements.data.market_data.summary}
          {entitlements.data.tier < 2 && (
            <Link to="/pricing" className="ml-2 text-brand-600 hover:underline dark:text-brand-400">
              {p.dataPlanUpgrade}
            </Link>
          )}
        </div>
      )}

      {symbol && timeframeOptions.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">{p.dataTimeframe}</span>
          <select
            className="input max-w-xs"
            value={activeTimeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          >
            {timeframeOptions.map((tf) => (
              <option key={tf} value={tf}>
                {tf}
              </option>
            ))}
          </select>
          {barCount != null && (
            <span className="text-xs text-slate-400">
              {barsCapped
                ? p.dataBarsCapped(barCount, activeDataset!.rows)
                : p.dataBars(barCount)}
            </span>
          )}
          {barsCapped && (
            <Link to="/pricing" className="text-xs text-brand-600 hover:underline dark:text-brand-400">
              {p.dataPlanHint}
            </Link>
          )}
        </div>
      )}

      {symbol && activeTimeframe && (
        <>
          <DataQualityBanner symbol={symbol} timeframe={activeTimeframe} />
          <VolRegimeBanner
            symbol={symbol}
            timeframe={activeTimeframe}
            enabled={!quality.data?.regime?.fit_score}
          />
        </>
      )}

      {id && (
        <FactorCatalogPanel
          projectId={id}
          symbol={symbol}
          timeframe={activeTimeframe}
          enabled={Boolean(factors.data && factors.data.length > 0)}
        />
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

      {done.backtest && !done.validation && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
          {p.warnBacktestOnly}
        </div>
      )}

      {quality.data && (
        <PublishFeedPreview quality={quality.data} published={proj.status === "published"} />
      )}

      {quality.data && <ProjectRegimePanel quality={quality.data} />}

      {quality.data?.attention_coaching && quality.data.attention_coaching.length > 0 && (
        <AttentionCoachPanel
          tips={quality.data.attention_coaching}
          onAction={handleMasteryAction}
        />
      )}

      {quality.data && (
        <MasteryPathPanel quality={quality.data} onAction={handleMasteryAction} />
      )}

      {quality.data && quality.data.coaching_tips && quality.data.coaching_tips.length > 0 && (
        <FailureCoachPanel tips={quality.data.coaching_tips} onAction={handleMasteryAction} />
      )}

      {quality.data && (
        <div
          id="mastery-quality"
          className={`mb-6 card border ${
            quality.data.passed
              ? "border-emerald-200 bg-emerald-50/40 dark:border-emerald-900 dark:bg-emerald-950/30"
              : "border-amber-200 bg-amber-50/40 dark:border-amber-900 dark:bg-amber-950/20"
          }`}
        >
          <p className="font-semibold text-slate-800 dark:text-slate-100">
            {quality.data.passed ? p.qualityPass : p.qualityFail}
          </p>
          {quality.data.scorecard && Object.keys(quality.data.scorecard).length > 0 && (
            <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <ScoreRow
                label={p.scoreOos}
                value={quality.data.scorecard.oos_sharpe}
                need={quality.data.thresholds?.min_oos_sharpe}
              />
              <ScoreRow
                label={p.scoreRobust}
                value={quality.data.scorecard.robustness_score}
                extra={quality.data.scorecard.robustness_grade as string | null}
                need={quality.data.thresholds?.min_robustness_score}
              />
              <ScoreRow
                label={p.scoreBacktest}
                value={quality.data.scorecard.backtest_sharpe}
                need={quality.data.thresholds?.min_backtest_sharpe}
              />
              <ScoreRow
                label={p.scoreSealed}
                value={quality.data.scorecard.sealed_holdout_sharpe}
                need={quality.data.thresholds?.min_sealed_holdout_sharpe}
              />
            </div>
          )}
          {!quality.data.passed && quality.data.reasons.length > 0 && (
            <ul className="mt-3 list-inside list-disc text-sm text-slate-600 dark:text-slate-300">
              {quality.data.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          {quality.data.hints && quality.data.hints.length > 0 && (
            <div className="mt-3 rounded-lg border border-slate-200 bg-white/60 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900/40">
              <p className="font-medium text-slate-700 dark:text-slate-200">{p.qualityHintsTitle}</p>
              <ul className="mt-1 list-inside list-disc text-slate-600 dark:text-slate-300">
                {quality.data.hints.map((h) => (
                  <li key={h}>{h}</li>
                ))}
              </ul>
            </div>
          )}
          {quality.data.orthogonal && (
            <p className="mt-3 text-xs text-slate-500">
              {p.orthogonalTitle}: {p.orthogonalVerdict(quality.data.orthogonal.verdict)}
              {quality.data.orthogonal.r2 != null &&
                ` (R² ${Number(quality.data.orthogonal.r2).toFixed(2)})`}
            </p>
          )}
          {!quality.data.passed && (
            <QualityCoach
              reasons={quality.data.reasons}
              onScrollToFactorLab={scrollToFactorLab}
              onRunValidation={() => runValidation.mutate()}
              canRunValidation={Boolean(projectFactor) && done.backtest && !done.validation}
              showDataPlanHint={
                (entitlements.data?.tier ?? 0) < 2 &&
                (barsCapped ||
                  quality.data.reasons.some(
                    (r) =>
                      r.includes("holdout") ||
                      r.includes("封印") ||
                      r.includes("样本外") ||
                      r.includes("OOS"),
                  ))
              }
            />
          )}
        </div>
      )}

      {done.backtest && (
        <div className="mb-6">
          <BacktestResultsPanel factorId={projectFactor?.id ?? null} enabled={done.backtest} />
        </div>
      )}

      {done.validation && (
        <div className="mb-6" id="validation-results">
          <ValidationResultsPanel factorId={projectFactor?.id ?? null} enabled={done.validation} />
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
                id={
                  s.key === "backtest"
                    ? "project-step-backtest"
                    : s.key === "validation"
                      ? "project-step-validation"
                      : s.key === "report"
                        ? "project-step-report"
                        : undefined
                }
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

      <div className="mt-4" id="factor-scan">
        <FactorScanPanel
          projectId={id}
          symbol={symbol}
          timeframe={activeTimeframe}
          factors={projectFactors}
        />
      </div>

      <div className="mt-4" id="factor-lab">
        <FactorLab projectId={id} symbol={symbol} timeframe={activeTimeframe} />
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

      <div className="mt-4" id="paper-tracking">
        <PaperTrackingPanel
          factorId={projectFactor?.id ?? null}
          enabled={done.validation}
          projectId={id}
          onRevalidate={() => handleMasteryAction("revalidate")}
        />
      </div>

      <div className="mt-4" id="paper-execution">
        <L4PortfolioTools
          projectId={id}
          paperFactorId={quality.data?.paper_ready ? (quality.data.factor_id ?? projectFactor?.id) : undefined}
          paperSymbol={quality.data?.paper_ready ? (quality.data.symbol ?? symbol) : undefined}
        />
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

function ScoreRow({
  label,
  value,
  need,
  extra,
}: {
  label: string;
  value: number | string | null | undefined;
  need?: number;
  extra?: string | null;
}) {
  const num = typeof value === "number" ? value : value != null ? Number(value) : null;
  const ok = need == null || need < -100 || (num != null && num >= need);
  const display =
    num != null && !Number.isNaN(num)
      ? num.toFixed(2)
      : value == null
        ? "—"
        : String(value);
  return (
    <div className={`rounded-md px-2 py-1 ${ok ? "" : "text-amber-800 dark:text-amber-200"}`}>
      <span className="text-slate-500">{label}: </span>
      <span className="font-medium">
        {display}
        {extra ? ` (${extra})` : ""}
      </span>
      {need != null && need > -100 && (
        <span className="text-xs text-slate-400"> / ≥{need}</span>
      )}
    </div>
  );
}

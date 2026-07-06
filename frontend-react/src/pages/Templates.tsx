import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listTemplates, getTemplateRegimePicks, startTemplate, trackEvent, getResearchJourney } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useFlow } from "../store/flow";
import { useLocale } from "../store/locale";
import { FIRST_PROJECT_WELCOME_KEY, FOLLOWING_PROJECT_REPLICATION_KEY, FOLLOWING_TEMPLATE_HANDOFF_KEY } from "../lib/onboardingFocus";
import { REGIME_TEMPLATE_SYMBOLS } from "../lib/templateHints";
import { attachReplicationBenchmarkToProject } from "../lib/replicationBenchmark";
import { useStartTemplateFlow } from "../lib/useStartTemplateFlow";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

const REGIME_SYMBOLS = ["RB", "AU", "IF"] as const;
type RegimeSymbol = (typeof REGIME_SYMBOLS)[number];

export default function Templates() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const setProject = useFlow((s) => s.setProject);
  const t = useLocale((s) => s.dict.templates);
  const c = useLocale((s) => s.dict.common);
  const [params, setParams] = useSearchParams();
  const focus = params.get("focus");
  const symbolParam = params.get("symbol");
  const initialSymbol: RegimeSymbol =
    symbolParam && REGIME_SYMBOLS.includes(symbolParam as RegimeSymbol)
      ? (symbolParam as RegimeSymbol)
      : "RB";
  const [regimeSymbol, setRegimeSymbol] = useState<RegimeSymbol>(initialSymbol);
  const [starting, setStarting] = useState<string | null>(null);
  const [highlightedFocus, setHighlightedFocus] = useState<string | null>(null);

  const setSymbol = (sym: RegimeSymbol) => {
    setRegimeSymbol(sym);
    const next = new URLSearchParams(params);
    if (sym === "RB") next.delete("symbol");
    else next.set("symbol", sym);
    setParams(next, { replace: true });
  };

  const templateList = useQuery({ queryKey: ["templates"], queryFn: listTemplates });
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const regimePicks = useQuery({
    queryKey: ["template-regime-picks", regimeSymbol],
    queryFn: () => getTemplateRegimePicks(regimeSymbol),
  });

  useEffect(() => {
    if (!focus || !templateList.data?.some((tpl) => tpl.code === focus)) return;
    const scrollTimer = window.setTimeout(() => {
      document.getElementById(`tpl-${focus}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      setHighlightedFocus(focus);
    }, 120);
    const clearTimer = window.setTimeout(() => setHighlightedFocus(null), 3200);
    return () => {
      window.clearTimeout(scrollTimer);
      window.clearTimeout(clearTimer);
    };
  }, [focus, templateList.data]);

  const recommendedCodes = new Set(regimePicks.data?.picks.map((p) => p.code) ?? []);
  const pickByCode = Object.fromEntries((regimePicks.data?.picks ?? []).map((p) => [p.code, p]));
  const focusedTpl = focus ? templateList.data?.find((tpl) => tpl.code === focus) : undefined;
  const focusedPick = focus ? pickByCode[focus] : undefined;
  const [focusCoachDismissed, setFocusCoachDismissed] = useState(false);
  const [masterHandoffDismissed, setMasterHandoffDismissed] = useState(false);
  const [masterHandoffSymbol, setMasterHandoffSymbol] = useState<string | null>(() =>
    typeof window !== "undefined" ? sessionStorage.getItem(FOLLOWING_TEMPLATE_HANDOFF_KEY) : null,
  );
  const showFocusCoach =
    Boolean(focusedTpl && focusedTpl.allowed !== false && !focusCoachDismissed);
  const showMasterHandoff =
    Boolean(
      masterHandoffSymbol &&
        !masterHandoffDismissed &&
        focus &&
        masterHandoffSymbol.toUpperCase() === regimeSymbol,
    );

  const clearMasterHandoff = () => {
    sessionStorage.removeItem(FOLLOWING_TEMPLATE_HANDOFF_KEY);
    setMasterHandoffSymbol(null);
    setMasterHandoffDismissed(true);
  };

  useEffect(() => {
    if (!masterHandoffSymbol) return;
    const sym = masterHandoffSymbol.trim().toUpperCase();
    if (!REGIME_TEMPLATE_SYMBOLS.has(sym) || sym === regimeSymbol) return;
    setSymbol(sym as RegimeSymbol);
  }, [masterHandoffSymbol, regimeSymbol]);

  const oneClickStart = useStartTemplateFlow({
    startedMessage: t.started,
    failMessage: t.startFail,
    from: "templates-banner",
  });

  const templateStepDone = journey.data?.steps.find((s) => s.key === "template")?.done ?? false;
  const quickstartPick = journey.data?.quickstart_guide?.recommended_template;
  const regimeTopPick = regimePicks.data?.picks[0];
  const oneClickCode = quickstartPick ?? regimeTopPick?.code ?? null;
  const oneClickTitle =
    journey.data?.quickstart_guide?.recommended_template_title ?? regimeTopPick?.title ?? null;
  const showOneClickBanner =
    !templateStepDone && Boolean(oneClickCode && oneClickTitle) && !showMasterHandoff && !showFocusCoach;

  const start = useMutation({
    mutationFn: (code: string) => startTemplate(code, true),
    onMutate: (code) => setStarting(code),
    onSuccess: (res) => {
      const fromReplication = Boolean(masterHandoffSymbol);
      void trackEvent("template_start", { template: res.template_code, from_replication: fromReplication });
      setProject(res.project_id, res.factor_id);
      sessionStorage.setItem(FIRST_PROJECT_WELCOME_KEY, res.project_id);
      if (fromReplication) {
        sessionStorage.setItem(FOLLOWING_PROJECT_REPLICATION_KEY, res.project_id);
        attachReplicationBenchmarkToProject(res.project_id);
      }
      sessionStorage.removeItem(FOLLOWING_TEMPLATE_HANDOFF_KEY);
      setMasterHandoffSymbol(null);
      void qc.invalidateQueries({ queryKey: ["projects"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      notify(t.started, "success");
      navigate(`/projects/${res.project_id}`);
    },
    onError: (err) => notify(apiErrorMessage(err, t.startFail), "error"),
    onSettled: () => setStarting(null),
  });

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle} />
      <p className="-mt-4 mb-4 text-xs text-slate-500 dark:text-slate-400">{t.catalogNote}</p>

      {showOneClickBanner && oneClickCode && oneClickTitle && (
        <div className="mb-6 rounded-xl border border-emerald-300 bg-gradient-to-r from-emerald-50/95 to-teal-50/70 p-4 shadow-sm dark:border-emerald-800 dark:from-emerald-950/40 dark:to-teal-950/30">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
            🚀 {t.oneClickBadge}
          </p>
          <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{t.oneClickTitle}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{t.oneClickMessage(oneClickTitle)}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-primary text-xs"
              disabled={oneClickStart.isPending}
              onClick={() => oneClickStart.mutate(oneClickCode)}
            >
              {oneClickStart.isPending ? c.starting : t.oneClickStart}
            </button>
            <button
              type="button"
              className="btn text-xs"
              onClick={() => {
                document.getElementById(`tpl-${oneClickCode}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
              }}
            >
              {t.oneClickBrowse}
            </button>
          </div>
        </div>
      )}

      {showMasterHandoff && masterHandoffSymbol && (
        <div className="mb-4 rounded-xl border border-teal-300 bg-gradient-to-r from-teal-50/95 to-cyan-50/70 p-4 dark:border-teal-800 dark:from-teal-950/40 dark:to-cyan-950/30">
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-800 dark:text-teal-200">
            📖 {t.masterHandoffBadge}
          </p>
          <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">
            {t.masterHandoffTitle(masterHandoffSymbol)}
          </p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{t.masterHandoffHint}</p>
          <button type="button" className="btn mt-3 text-xs" onClick={clearMasterHandoff}>
            {t.masterHandoffDismiss}
          </button>
        </div>
      )}

      {showFocusCoach && focusedTpl && focus && (
        <div className="mb-6 rounded-xl border border-brand-300 bg-gradient-to-r from-brand-50/90 to-violet-50/60 p-4 shadow-sm dark:border-brand-800 dark:from-brand-950/40 dark:to-violet-950/30">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-700 dark:text-brand-300">
                🤖 {t.focusCoachBadge}
              </p>
              <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{focusedTpl.title}</p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                {t.focusCoachHint(focusedTpl.title)}
              </p>
              {focusedPick && (
                <p className="mt-1 text-xs text-violet-700 dark:text-violet-300">
                  {t.regimeFit(focusedPick.fit_verdict, focusedPick.fit_score)}
                  {" · "}
                  {focusedPick.fit_hint}
                </p>
              )}
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              <button
                type="button"
                className="btn-primary whitespace-nowrap"
                disabled={start.isPending}
                onClick={() => start.mutate(focus)}
              >
                {starting === focus ? c.starting : t.focusCoachStart}
              </button>
              <button
                type="button"
                className="btn whitespace-nowrap"
                onClick={() => setFocusCoachDismissed(true)}
              >
                {t.focusCoachBrowse}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mb-6 rounded-xl border border-brand-100 bg-brand-50/50 p-4 dark:border-brand-900 dark:bg-brand-950/30">
        <p className="font-medium text-brand-800 dark:text-brand-200">{t.pathTitle}</p>
        <ol className="mt-2 list-inside list-decimal space-y-1 text-sm text-slate-600 dark:text-slate-300">
          {t.pathSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      {regimePicks.data && (regimePicks.data.picks.length > 0 || regimePicks.data.coach_hint) && (
        <div className="mb-6 rounded-xl border border-violet-200 bg-violet-50/50 p-4 dark:border-violet-900 dark:bg-violet-950/30">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-violet-800/80 dark:text-violet-200/80">{t.regimeSymbolHint}</p>
            <div className="flex flex-wrap gap-1">
              {REGIME_SYMBOLS.map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => setSymbol(sym)}
                  className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
                    regimeSymbol === sym
                      ? "bg-violet-600 text-white"
                      : "bg-white text-violet-800 ring-1 ring-violet-200 hover:bg-violet-100 dark:bg-slate-900 dark:text-violet-200 dark:ring-violet-800"
                  }`}
                >
                  {t.regimeSymbol(sym)}
                </button>
              ))}
            </div>
          </div>
          <p className="font-medium text-violet-900 dark:text-violet-100">
            {regimePicks.data.regime_label
              ? t.regimePickTitle(regimePicks.data.regime_label, regimePicks.data.symbol)
              : t.regimePickFallback}
          </p>
          <p className="mt-1 text-sm text-violet-800/90 dark:text-violet-200/90">
            {regimePicks.data.coach_hint}
          </p>
          {regimePicks.data.picks.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {regimePicks.data.picks.map((pick) => (
                <button
                  key={pick.code}
                  type="button"
                  className="rounded-lg border border-violet-300 bg-white px-3 py-2 text-left text-xs transition hover:border-brand-400 dark:border-violet-800 dark:bg-slate-900"
                  onClick={() => {
                    document.getElementById(`tpl-${pick.code}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
                  }}
                >
                  <span className="font-semibold text-slate-800 dark:text-slate-100">{pick.title}</span>
                  <span className="ml-2 text-violet-700 dark:text-violet-300">
                    {t.regimeFit(pick.fit_verdict, pick.fit_score)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {templateList.isLoading ? (
        <Spinner />
      ) : templateList.isError ? (
        <ErrorBox message={apiErrorMessage(templateList.error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...(templateList.data ?? [])]
            .sort((a, b) => {
              const aSym = a.symbol === regimeSymbol ? 0 : 1;
              const bSym = b.symbol === regimeSymbol ? 0 : 1;
              const aRec = recommendedCodes.has(a.code) ? 0 : 1;
              const bRec = recommendedCodes.has(b.code) ? 0 : 1;
              return aSym - bSym || aRec - bRec;
            })
            .map((tpl) => {
            const locked = tpl.allowed === false;
            const trackLabel =
              tpl.track === "master"
                ? t.trackMaster
                : tpl.track === "advanced"
                  ? t.trackAdvanced
                  : t.trackBeginner;
            return (
              <div
                key={tpl.code}
                id={`tpl-${tpl.code}`}
                className={`card relative flex flex-col ${
                  focus === tpl.code || highlightedFocus === tpl.code
                    ? "ring-2 ring-brand-400 shadow-lg shadow-brand-200/50 dark:shadow-brand-900/30"
                    : ""
                } ${locked ? "opacity-90" : ""} ${
                  recommendedCodes.has(tpl.code) ? "ring-2 ring-violet-300 dark:ring-violet-800" : ""
                }`}
              >
                {recommendedCodes.has(tpl.code) && (
                  <span className="absolute left-3 top-3 rounded-full bg-violet-600 px-2 py-0.5 text-[10px] font-medium text-white">
                    {t.regimeRecommended}
                  </span>
                )}
                {tpl.symbol === regimeSymbol && !recommendedCodes.has(tpl.code) && (
                  <span className="absolute left-3 top-3 rounded-full bg-slate-600 px-2 py-0.5 text-[10px] font-medium text-white dark:bg-slate-700">
                    {t.regimeSymbolMatch}
                  </span>
                )}
                {locked && (
                  <span className="absolute right-3 top-3 rounded-full bg-slate-800 px-2 py-0.5 text-xs text-white dark:bg-slate-700">
                    🔒 {c.locked}
                  </span>
                )}
                <div className="flex items-center justify-between gap-2 pr-16">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-100">
                    {tpl.title}
                  </h3>
                  <div className="flex shrink-0 gap-1">
                    <span
                      className={`badge ${
                        tpl.track === "master"
                          ? "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                          : tpl.track === "advanced"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                            : ""
                      }`}
                    >
                      {trackLabel}
                    </span>
                    <span className="badge">{tpl.symbol}</span>
                  </div>
                </div>
                {tpl.suitable_for && (
                  <p className="mt-2 text-xs font-medium text-brand-600 dark:text-brand-400">
                    {t.suitableFor}: {tpl.suitable_for}
                  </p>
                )}
                {pickByCode[tpl.code] && (
                  <p className="mt-1 text-xs text-violet-700 dark:text-violet-300">
                    {t.regimeFit(pickByCode[tpl.code].fit_verdict, pickByCode[tpl.code].fit_score)}
                    {" · "}
                    {pickByCode[tpl.code].fit_hint}
                  </p>
                )}
                <p className="mt-2 flex-1 text-sm text-slate-500">{tpl.description}</p>
                <p className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-800">
                  💡 {c.hypothesis}: {tpl.hypothesis}
                </p>
                {tpl.factor_note && (
                  <p className="mt-2 rounded-lg border border-slate-200 bg-white/70 px-3 py-2 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300">
                    <span className="font-medium">{t.factorSetup}: </span>
                    {tpl.factor_note}
                  </p>
                )}
                {tpl.how_it_works && (
                  <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    <span className="font-medium text-slate-600 dark:text-slate-300">{t.howWorks} </span>
                    {tpl.how_it_works}
                  </p>
                )}
                {tpl.learning_steps && tpl.learning_steps.length > 0 && (
                  <div className="mt-2 rounded-lg border border-brand-100 bg-brand-50/40 px-3 py-2 dark:border-brand-900 dark:bg-brand-950/20">
                    <p className="text-xs font-medium text-brand-700 dark:text-brand-300">{t.youWill}</p>
                    <ol className="mt-1 list-inside list-decimal space-y-0.5 text-xs text-slate-600 dark:text-slate-300">
                      {tpl.learning_steps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {tpl.tags.map((tag) => (
                    <span key={tag} className="badge">
                      #{tag}
                    </span>
                  ))}
                </div>
                {locked ? (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs text-amber-700 dark:text-amber-300">
                      {t.lockedHint}
                      {tpl.lock_hint ? ` (${tpl.lock_hint})` : ""}
                    </p>
                    <Link to="/pricing" className="btn-ghost w-full text-center">
                      {c.upgradePlans}
                    </Link>
                  </div>
                ) : (
                  <button
                    className="btn-primary mt-4"
                    disabled={start.isPending}
                    onClick={() => start.mutate(tpl.code)}
                  >
                    {starting === tpl.code ? c.starting : c.startNow}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listTemplates, getTemplateRegimePicks, startTemplate, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useFlow } from "../store/flow";
import { useLocale } from "../store/locale";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Templates() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const setProject = useFlow((s) => s.setProject);
  const t = useLocale((s) => s.dict.templates);
  const c = useLocale((s) => s.dict.common);
  const [params] = useSearchParams();
  const focus = params.get("focus");
  const [starting, setStarting] = useState<string | null>(null);

  const templates = useQuery({ queryKey: ["templates"], queryFn: listTemplates });
  const regimePicks = useQuery({
    queryKey: ["template-regime-picks"],
    queryFn: () => getTemplateRegimePicks("RB"),
  });

  const recommendedCodes = new Set(regimePicks.data?.picks.map((p) => p.code) ?? []);
  const pickByCode = Object.fromEntries((regimePicks.data?.picks ?? []).map((p) => [p.code, p]));

  const start = useMutation({
    mutationFn: (code: string) => startTemplate(code, true),
    onMutate: (code) => setStarting(code),
    onSuccess: (res) => {
      void trackEvent("template_start", { template: res.template_code });
      setProject(res.project_id, res.factor_id);
      void qc.invalidateQueries({ queryKey: ["projects"] });
      notify(t.started, "success");
      navigate(`/projects/${res.project_id}`);
    },
    onError: (err) => notify(apiErrorMessage(err, t.startFail), "error"),
    onSettled: () => setStarting(null),
  });

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle} />

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

      {templates.isLoading ? (
        <Spinner />
      ) : templates.isError ? (
        <ErrorBox message={apiErrorMessage(templates.error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.data?.map((tpl) => {
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
                  focus === tpl.code ? "ring-2 ring-brand-400" : ""
                } ${locked ? "opacity-90" : ""} ${
                  recommendedCodes.has(tpl.code) ? "ring-2 ring-violet-300 dark:ring-violet-800" : ""
                }`}
              >
                {recommendedCodes.has(tpl.code) && (
                  <span className="absolute left-3 top-3 rounded-full bg-violet-600 px-2 py-0.5 text-[10px] font-medium text-white">
                    {t.regimeRecommended}
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

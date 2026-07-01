import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listTemplates, startTemplate, trackEvent } from "../api/endpoints";
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
      {templates.isLoading ? (
        <Spinner />
      ) : templates.isError ? (
        <ErrorBox message={apiErrorMessage(templates.error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.data?.map((tpl) => {
            const locked = tpl.allowed === false;
            return (
              <div
                key={tpl.code}
                className={`card relative flex flex-col ${
                  focus === tpl.code ? "ring-2 ring-brand-400" : ""
                } ${locked ? "opacity-90" : ""}`}
              >
                {locked && (
                  <span className="absolute right-3 top-3 rounded-full bg-slate-800 px-2 py-0.5 text-xs text-white dark:bg-slate-700">
                    🔒 {c.locked}
                  </span>
                )}
                <div className="flex items-center justify-between gap-2 pr-16">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-100">
                    {tpl.title}
                  </h3>
                  <span className="badge shrink-0">{tpl.symbol}</span>
                </div>
                <p className="mt-2 flex-1 text-sm text-slate-500">{tpl.description}</p>
                <p className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-800">
                  💡 {c.hypothesis}: {tpl.hypothesis}
                </p>
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

import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listTemplates, startTemplate, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useFlow } from "../store/flow";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Templates() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const setProject = useFlow((s) => s.setProject);
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
      notify("项目已创建, 继续完成研究!", "success");
      navigate(`/projects/${res.project_id}`);
    },
    onError: (err) => notify(apiErrorMessage(err, "开局失败"), "error"),
    onSettled: () => setStarting(null),
  });

  return (
    <div>
      <PageTitle
        title="研究模板库"
        subtitle="选一个模板一键开局, 系统自动建好项目和起步因子。"
      />
      {templates.isLoading ? (
        <Spinner />
      ) : templates.isError ? (
        <ErrorBox message={apiErrorMessage(templates.error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.data?.map((t) => (
            <div
              key={t.code}
              className={`card flex flex-col ${
                focus === t.code ? "ring-2 ring-brand-400" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">{t.title}</h3>
                <span className="badge">{t.symbol}</span>
              </div>
              <p className="mt-2 flex-1 text-sm text-slate-500">{t.description}</p>
              <p className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
                💡 假设: {t.hypothesis}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {t.tags.map((tag) => (
                  <span key={tag} className="badge">
                    #{tag}
                  </span>
                ))}
              </div>
              <button
                className="btn-primary mt-4"
                disabled={start.isPending}
                onClick={() => start.mutate(t.code)}
              >
                {starting === t.code ? "开局中…" : "一键开局"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

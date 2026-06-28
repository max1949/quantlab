import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createBacktest,
  createValidation,
  generateReport,
  getGraph,
  getProject,
  listFactors,
  publishProject,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import type { Graph } from "../api/types";

type StepKey = "factor" | "backtest" | "validation" | "report" | "publish";

export default function ProjectDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);

  const project = useQuery({ queryKey: ["project", id], queryFn: () => getProject(id) });
  const factors = useQuery({ queryKey: ["factors"], queryFn: listFactors });
  const graph = useQuery({ queryKey: ["graph", id], queryFn: () => getGraph(id) });

  const projectFactor = useMemo(
    () => factors.data?.find((f) => f.project_id === id) ?? null,
    [factors.data, id],
  );

  const symbol = project.data?.symbol || "";

  const done = useMemo(() => computeDone(graph.data, project.data?.status), [
    graph.data,
    project.data?.status,
  ]);

  const [busy, setBusy] = useState<StepKey | null>(null);

  function refreshAll() {
    void qc.invalidateQueries({ queryKey: ["graph", id] });
    void qc.invalidateQueries({ queryKey: ["project", id] });
    void qc.invalidateQueries({ queryKey: ["projects"] });
  }

  const runBacktest = useMutation({
    mutationFn: () =>
      createBacktest({ factor_id: projectFactor!.id, symbol }),
    onMutate: () => setBusy("backtest"),
    onSuccess: (bt) => {
      void trackEvent("backtest_run", { project: id, status: bt.status });
      notify(`回测完成 (${bt.status})`, "success");
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, "回测失败"), "error"),
    onSettled: () => setBusy(null),
  });

  const runValidation = useMutation({
    mutationFn: () =>
      createValidation({ factor_id: projectFactor!.id, symbol }),
    onMutate: () => setBusy("validation"),
    onSuccess: (v) => {
      void trackEvent("validation_run", { project: id, status: v.status });
      notify(`科学验证完成 (${v.status})`, "success");
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, "验证失败"), "error"),
    onSettled: () => setBusy(null),
  });

  const genReport = useMutation({
    mutationFn: () => generateReport({ project_id: id }),
    onMutate: () => setBusy("report"),
    onSuccess: (r) => {
      void trackEvent("report_generated", { project: id });
      notify("研究报告已生成!", "success");
      refreshAll();
      navigate(`/reports/${r.id}`);
    },
    onError: (e) => notify(apiErrorMessage(e, "生成报告失败"), "error"),
    onSettled: () => setBusy(null),
  });

  const publish = useMutation({
    mutationFn: () => publishProject(id),
    onMutate: () => setBusy("publish"),
    onSuccess: () => {
      void trackEvent("project_published", { project: id });
      notify("项目已发布到研究广场!", "success");
      refreshAll();
    },
    onError: (e) => notify(apiErrorMessage(e, "发布失败"), "error"),
    onSettled: () => setBusy(null),
  });

  if (project.isLoading) return <Spinner />;
  if (project.isError)
    return <ErrorBox message={apiErrorMessage(project.error, "项目不存在")} />;

  const p = project.data!;

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
      title: "1. 起步因子",
      desc: projectFactor
        ? `已就绪: ${projectFactor.name}`
        : "该项目还没有因子",
      cta: "已完成",
      pending: false,
      disabled: true,
    },
    {
      key: "backtest",
      title: "2. 跑回测",
      desc: "看因子在历史行情上的表现",
      cta: "运行回测",
      run: () => runBacktest.mutate(),
      pending: busy === "backtest",
      disabled: !projectFactor || done.backtest,
    },
    {
      key: "validation",
      title: "3. 科学验证",
      desc: "样本外 + Walk-Forward 检验是否过拟合",
      cta: "运行验证",
      run: () => runValidation.mutate(),
      pending: busy === "validation",
      disabled: !projectFactor || !done.backtest || done.validation,
    },
    {
      key: "report",
      title: "4. 生成研究报告",
      desc: "聚合因子+回测+验证, 写成人话报告",
      cta: "生成报告",
      run: () => genReport.mutate(),
      pending: busy === "report",
      disabled: !done.backtest,
    },
    {
      key: "publish",
      title: "5. 发布分享",
      desc: "公开到研究广场, 让更多人看到",
      cta: p.status === "published" ? "已发布" : "发布项目",
      run: () => publish.mutate(),
      pending: busy === "publish",
      disabled: !done.report || p.status === "published",
    },
  ];

  return (
    <div>
      <PageTitle title={p.title} subtitle={p.question || p.description} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="badge">状态 {p.status}</span>
        {p.symbol && <span className="badge">标的 {p.symbol}</span>}
        {p.tags?.map((t) => (
          <span key={t} className="badge">
            #{t}
          </span>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* 引导步骤 */}
        <div className="space-y-3">
          {steps.map((s) => {
            const finished = done[s.key as keyof typeof done];
            return (
              <div
                key={s.key}
                className={`card flex items-center justify-between ${
                  finished ? "border-emerald-200 bg-emerald-50/40" : ""
                }`}
              >
                <div>
                  <p className="font-semibold text-slate-800">
                    {finished && "✅ "}
                    {s.title}
                  </p>
                  <p className="text-sm text-slate-500">{s.desc}</p>
                </div>
                {s.run && (
                  <button
                    className="btn-primary whitespace-nowrap"
                    disabled={s.disabled || s.pending}
                    onClick={s.run}
                  >
                    {s.pending ? "运行中…" : s.cta}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* 研究路径图谱 */}
        <div className="card">
          <h3 className="mb-3 font-semibold">研究路径图谱</h3>
          {graph.isLoading ? (
            <Spinner />
          ) : graph.data && graph.data.nodes.length > 0 ? (
            <GraphView graph={graph.data} />
          ) : (
            <p className="py-6 text-center text-sm text-slate-400">
              完成上面的步骤, 这里会自动画出你的研究路径
            </p>
          )}
        </div>
      </div>

      <p className="mt-6 text-sm text-slate-400">
        <Link to="/projects" className="text-brand-600">
          ← 返回项目列表
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
  // 图谱节点用 ref_type 区分实际产物 (factor/backtest/validation/report)。
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

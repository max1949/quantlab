import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  createFormulaFactor,
  createPythonFactor,
  createStackFactor,
  createTemplateFactor,
  getEntitlements,
  getFactorTemplates,
  getFormulaHelp,
  getPythonFactorHelp,
  listFactors,
  previewFactor,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { Spinner } from "./ui";
import type { Factor, FactorPreview, FeatureState } from "../api/types";

export default function FactorLab({ projectId }: { projectId: string }) {
  const user = useAuth((s) => s.user)!;
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const fl = useLocale((s) => s.dict.factorLab);
  const c = useLocale((s) => s.dict.common);

  const templates = useQuery({
    queryKey: ["factor-templates"],
    queryFn: getFactorTemplates,
  });
  const factors = useQuery({ queryKey: ["factors"], queryFn: listFactors });
  const entitlements = useQuery({
    queryKey: ["entitlements"],
    queryFn: getEntitlements,
  });
  const formulaFeat = entitlements.data?.features.find(
    (f) => f.key === "factor_formula",
  );
  const pythonFeat = entitlements.data?.features.find(
    (f) => f.key === "factor_python",
  );
  const projectFactors = useMemo(
    () => (factors.data ?? []).filter((f) => f.project_id === projectId),
    [factors.data, projectId],
  );

  const [mode, setMode] = useState<"template" | "stack" | "formula" | "python">("template");
  const [preview, setPreview] = useState<Record<string, FactorPreview>>({});

  function refresh() {
    void qc.invalidateQueries({ queryKey: ["factors"] });
    void qc.invalidateQueries({ queryKey: ["graph", projectId] });
  }

  const doPreview = useMutation({
    mutationFn: (id: string) => previewFactor(id),
    onSuccess: (p) => setPreview((m) => ({ ...m, [p.factor_id]: p })),
    onError: (e) => notify(apiErrorMessage(e, fl.previewFailed), "error"),
  });

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">{fl.title}</h3>
        <div className="flex gap-1">
          <button
            onClick={() => setMode("template")}
            className={`rounded-lg px-3 py-1 text-sm ${mode === "template" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            {fl.template}
          </button>
          <button
            onClick={() => setMode("stack")}
            className={`rounded-lg px-3 py-1 text-sm ${mode === "stack" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            {fl.stack}
          </button>
          <button
            onClick={() => setMode("formula")}
            className={`rounded-lg px-3 py-1 text-sm ${mode === "formula" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            {fl.formula}{!formulaFeat?.allowed && " 🔒"}
          </button>
          <button
            onClick={() => setMode("python")}
            className={`rounded-lg px-3 py-1 text-sm ${mode === "python" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            {fl.python}{!pythonFeat?.allowed && " 🔒"}
          </button>
        </div>
      </div>

      <div className="mb-4">
        <p className="mb-2 text-xs font-medium text-slate-400">{fl.projectFactors}</p>
        {factors.isLoading ? (
          <Spinner />
        ) : projectFactors.length > 0 ? (
          <ul className="space-y-2">
            {projectFactors.map((f) => (
              <li key={f.id} className="rounded-lg border border-slate-200 px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">
                    {f.name}{" "}
                    <span className="badge ml-1">
                      {f.kind === "stack"
                        ? fl.stackKind
                        : f.kind === "formula"
                          ? fl.formula
                          : f.kind === "python"
                            ? fl.python
                            : f.template_type}
                    </span>
                  </span>
                  <button
                    className="text-xs text-brand-600"
                    onClick={() => doPreview.mutate(f.id)}
                  >
                    {c.preview}
                  </button>
                </div>
                {preview[f.id] && <PreviewStats p={preview[f.id]} />}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-400">{fl.noFactors}</p>
        )}
      </div>

      {mode === "template" && (
        <TemplateForm
          projectId={projectId}
          templatesLoading={templates.isLoading}
          templates={templates.data ?? []}
          onCreated={refresh}
        />
      )}
      {mode === "stack" && (
        <StackForm
          projectId={projectId}
          level={user.level}
          factors={projectFactors}
          onCreated={refresh}
        />
      )}
      {mode === "formula" &&
        (formulaFeat?.allowed ? (
          <FormulaForm projectId={projectId} onCreated={refresh} />
        ) : (
          <FeatureLock feat={formulaFeat} lockedText={fl.formulaLocked} />
        ))}
      {mode === "python" &&
        (pythonFeat?.allowed ? (
          <PythonForm projectId={projectId} onCreated={refresh} />
        ) : (
          <FeatureLock feat={pythonFeat} lockedText={fl.pythonLocked} />
        ))}
    </div>
  );
}

function FeatureLock({ feat, lockedText }: { feat?: FeatureState; lockedText: string }) {
  const f = useLocale((s) => s.dict.factorLab);
  const c = useLocale((s) => s.dict.common);
  return (
    <div className="rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
      <p className="mb-2 font-medium">🔒 {lockedText}</p>
      {feat && (
        <ul className="mb-3 space-y-1 text-amber-700">
          <li>
            {feat.level_ok ? "✓" : "•"} {f.capability}: {feat.min_level_name}
            {feat.level_ok ? ` ${f.met}` : ` ${f.notYet}`}
          </li>
          <li>
            {feat.tier_ok ? "✓" : "•"} {f.membership}: {feat.min_tier_name}
            {feat.tier_ok ? ` ${f.tierActive}` : ` ${f.tierInactive}`}
          </li>
        </ul>
      )}
      <Link to="/pricing" className="btn-primary inline-block">
        {c.upgradePlans} →
      </Link>
    </div>
  );
}

function FormulaForm({
  projectId,
  onCreated,
}: {
  projectId: string;
  onCreated: () => void;
}) {
  const notify = useUi((s) => s.notify);
  const help = useQuery({ queryKey: ["formula-help"], queryFn: getFormulaHelp });
  const [name, setName] = useState("");
  const [expr, setExpr] = useState("");

  const create = useMutation({
    mutationFn: () =>
      createFormulaFactor({
        name: name.trim() || "公式因子",
        expr: expr.trim(),
        project_id: projectId,
      }),
    onSuccess: () => {
      void trackEvent("factor_created", { project: projectId, type: "formula" });
      notify("公式因子已创建", "success");
      setExpr("");
      onCreated();
    },
    onError: (e) => notify(apiErrorMessage(e, "创建失败"), "error"),
  });

  return (
    <div className="space-y-3 rounded-lg bg-slate-50 p-3">
      <div>
        <label className="label">因子公式</label>
        <textarea
          className="input font-mono text-sm"
          rows={2}
          placeholder="(close - sma(close, 20)) / std(close, 20)"
          value={expr}
          onChange={(e) => setExpr(e.target.value)}
        />
      </div>

      {help.data && (
        <details className="text-xs text-slate-500">
          <summary className="cursor-pointer text-brand-600">
            可用变量 / 函数 / 示例
          </summary>
          <div className="mt-2 space-y-2">
            <div>
              <b>变量:</b> {help.data.variables.join(", ")}
            </div>
            <div>
              <b>函数:</b>
              <ul className="mt-1 grid grid-cols-1 gap-0.5 sm:grid-cols-2">
                {help.data.functions.map((f) => (
                  <li key={f.name}>
                    <code className="text-slate-700">{f.name}</code> — {f.desc}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <b>示例 (点击填入):</b>
              <ul className="mt-1 space-y-0.5">
                {help.data.examples.map((ex) => (
                  <li key={ex}>
                    <button
                      className="text-left font-mono text-brand-600 hover:underline"
                      onClick={() => setExpr(ex)}
                    >
                      {ex}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </details>
      )}

      <div>
        <label className="label">因子名称</label>
        <input
          className="input"
          placeholder="我的公式因子"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      <button
        className="btn-primary w-full"
        disabled={create.isPending || !expr.trim()}
        onClick={() => create.mutate()}
      >
        {create.isPending ? "创建中…" : "创建公式因子"}
      </button>
    </div>
  );
}

function PythonForm({
  projectId,
  onCreated,
}: {
  projectId: string;
  onCreated: () => void;
}) {
  const notify = useUi((s) => s.notify);
  const fl = useLocale((s) => s.dict.factorLab);
  const help = useQuery({ queryKey: ["python-help"], queryFn: getPythonFactorHelp });
  const [name, setName] = useState("");
  const [source, setSource] = useState("");

  useEffect(() => {
    if (help.data?.template && !source) {
      setSource(help.data.template);
    }
  }, [help.data, source]);

  const create = useMutation({
    mutationFn: () =>
      createPythonFactor({
        name: name.trim() || "Python factor",
        source: source.trim(),
        project_id: projectId,
      }),
    onSuccess: () => {
      void trackEvent("factor_created", { project: projectId, type: "python" });
      notify(fl.factorCreated, "success");
      onCreated();
    },
    onError: (e) => notify(apiErrorMessage(e, fl.createFailed), "error"),
  });

  return (
    <div className="space-y-3 rounded-lg bg-slate-50 p-3">
      <div>
        <label className="label">Python {fl.python}</label>
        <textarea
          className="input font-mono text-sm"
          rows={8}
          value={source}
          onChange={(e) => setSource(e.target.value)}
        />
      </div>
      {help.data && (
        <details className="text-xs text-slate-500">
          <summary className="cursor-pointer text-brand-600">{fl.pythonTemplate}</summary>
          <ul className="mt-2 list-inside list-disc">
            {help.data.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </details>
      )}
      <div>
        <label className="label">{fl.factorName}</label>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <button
        className="btn-primary w-full"
        disabled={create.isPending || !source.trim()}
        onClick={() => create.mutate()}
      >
        {create.isPending ? "…" : fl.createPython}
      </button>
    </div>
  );
}

function PreviewStats({ p }: { p: FactorPreview }) {
  const entries = Object.entries(p.stats).slice(0, 6);
  return (
    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
      {entries.map(([k, v]) => (
        <div key={k} className="rounded bg-slate-50 px-2 py-1">
          <div className="text-slate-400">{k}</div>
          <div className="font-medium text-slate-700">
            {v === null ? "—" : Number(v).toFixed(3)}
          </div>
        </div>
      ))}
    </div>
  );
}

function TemplateForm({
  projectId,
  templates,
  templatesLoading,
  onCreated,
}: {
  projectId: string;
  templates: import("../api/types").FactorTemplateMeta[];
  templatesLoading: boolean;
  onCreated: () => void;
}) {
  const notify = useUi((s) => s.notify);
  const fl = useLocale((s) => s.dict.factorLab);
  const c = useLocale((s) => s.dict.common);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [params, setParams] = useState<Record<string, number>>({});

  const selected = templates.find((t) => t.code === code) ?? templates[0];

  // 模板加载后初始化默认选择 (用 effect, 避免 render 期 setState)。
  useEffect(() => {
    if (!code && templates.length > 0) {
      const t = templates.find((x) => x.allowed !== false) ?? templates[0];
      setCode(t.code);
      const init: Record<string, number> = {};
      t.params.forEach((p) => (init[p.name] = p.default));
      setParams(init);
      setName(t.label);
    }
  }, [code, templates]);

  const create = useMutation({
    mutationFn: () =>
      createTemplateFactor({
        name: name.trim() || selected.label,
        template_type: selected.code,
        params,
        project_id: projectId,
      }),
    onSuccess: () => {
      void trackEvent("factor_created", { project: projectId, type: selected?.code });
      notify(fl.factorCreated, "success");
      onCreated();
    },
    onError: (e) => notify(apiErrorMessage(e, fl.createFailed), "error"),
  });

  if (templatesLoading) return <Spinner />;
  if (!selected) return <p className="text-sm text-slate-400">{fl.noTemplates}</p>;

  const locked = selected && selected.allowed === false;

  return (
    <div className="space-y-3 rounded-lg bg-slate-50 p-3 dark:bg-slate-800/50">
      <div>
        <label className="label">{fl.pickTemplate}</label>
        <select
          className="input"
          value={selected.code}
          onChange={(e) => {
            const t = templates.find((x) => x.code === e.target.value)!;
            setCode(t.code);
            const init: Record<string, number> = {};
            t.params.forEach((p) => (init[p.name] = p.default));
            setParams(init);
            setName(t.label);
          }}
        >
          {templates.map((t) => (
            <option key={t.code} value={t.code}>
              {t.label}
              {t.allowed === false ? " 🔒" : ""} — {t.description}
            </option>
          ))}
        </select>
      </div>

      {locked ? (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">
          <p className="mb-2">{fl.templateLocked}</p>
          <Link to="/pricing" className="font-medium text-brand-600">
            {c.upgradePlans} →
          </Link>
        </div>
      ) : (
        <>
      {selected.params.map((p) => (
        <div key={p.name}>
          <label className="label">
            {p.label} ({p.min}–{p.max}): <b>{params[p.name] ?? p.default}</b>
          </label>
          <input
            type="range"
            className="w-full"
            min={p.min}
            max={p.max}
            value={params[p.name] ?? p.default}
            onChange={(e) =>
              setParams((m) => ({ ...m, [p.name]: Number(e.target.value) }))
            }
          />
        </div>
      ))}

      <div>
        <label className="label">因子名称</label>
        <input
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      <button
        className="btn-primary w-full"
        disabled={create.isPending}
        onClick={() => create.mutate()}
      >
        {create.isPending ? "Creating…" : "Create factor"}
      </button>
        </>
      )}
    </div>
  );
}

function StackForm({
  projectId,
  level,
  factors,
  onCreated,
}: {
  projectId: string;
  level: number;
  factors: Factor[];
  onCreated: () => void;
}) {
  const notify = useUi((s) => s.notify);
  const [name, setName] = useState("组合因子");
  const [weights, setWeights] = useState<Record<string, number>>({});

  const create = useMutation({
    mutationFn: () => {
      const components = Object.entries(weights)
        .filter(([, w]) => w !== 0)
        .map(([factor_id, weight]) => ({ factor_id, weight }));
      return createStackFactor({ name: name.trim() || "组合因子", components, project_id: projectId });
    },
    onSuccess: () => {
      void trackEvent("factor_created", { project: projectId, type: "stack" });
      notify("组合因子已创建", "success");
      onCreated();
    },
    onError: (e) => notify(apiErrorMessage(e, "创建失败"), "error"),
  });

  if (level < 1) {
    return (
      <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
        组合因子需要 L1（研究学徒）等级。先多做几次研究升级后即可解锁。
      </div>
    );
  }
  if (factors.length < 2) {
    return (
      <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">
        至少要有 2 个模板因子才能组合。先在「模板因子」里多建几个。
      </p>
    );
  }

  const chosen = Object.values(weights).filter((w) => w !== 0).length;

  return (
    <div className="space-y-3 rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-400">给因子设权重 (0 表示不参与), 至少选 1 个。</p>
      {factors.map((f) => (
        <div key={f.id} className="flex items-center gap-2">
          <span className="flex-1 truncate text-sm text-slate-700">{f.name}</span>
          <input
            type="number"
            step="0.1"
            className="input w-24"
            value={weights[f.id] ?? 0}
            onChange={(e) =>
              setWeights((m) => ({ ...m, [f.id]: Number(e.target.value) }))
            }
          />
        </div>
      ))}
      <div>
        <label className="label">组合名称</label>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <button
        className="btn-primary w-full"
        disabled={create.isPending || chosen < 1}
        onClick={() => create.mutate()}
      >
        {create.isPending ? "创建中…" : "创建组合因子"}
      </button>
    </div>
  );
}

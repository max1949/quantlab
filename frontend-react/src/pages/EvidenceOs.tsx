import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  diffOsStrategies,
  getOsDna,
  getOsExperiment,
  getOsGovernor,
  getOsLiveReadiness,
  getOsShadow,
  getOsStrategy,
  listOsExperiments,
  listOsStrategies,
  reproduceOsExperiment,
  runOsEvidence,
  runOsFactorSignPaper,
} from "../api/researchOs";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { PageTitle, Spinner } from "../components/ui";

type Tab =
  | "evidence"
  | "spec"
  | "experiments"
  | "paper"
  | "shadow"
  | "governor"
  | "dna"
  | "readiness";

const TABS: { id: Tab; label: string }[] = [
  { id: "evidence", label: "证据判定" },
  { id: "spec", label: "策略规格" },
  { id: "experiments", label: "实验账本" },
  { id: "paper", label: "模拟交易" },
  { id: "shadow", label: "影子对照" },
  { id: "governor", label: "组合治理" },
  { id: "dna", label: "DNA/坟场" },
  { id: "readiness", label: "实盘资格" },
];

export default function EvidenceOs() {
  const notify = useUi((s) => s.notify);
  const [tab, setTab] = useState<Tab>("evidence");
  const [strategyId, setStrategyId] = useState("hist_fl_momentum_w20");
  const [instrument, setInstrument] = useState("RB");
  const [selectedExp, setSelectedExp] = useState<string | null>(null);

  const strategies = useQuery({ queryKey: ["os-strategies"], queryFn: listOsStrategies });

  const evidence = useMutation({
    mutationFn: () => runOsEvidence({ strategy_id: strategyId, instrument, bars: 504 }),
    onError: (e) => notify(apiErrorMessage(e, "证据流水线失败"), "error"),
  });

  const paper = useMutation({
    mutationFn: () => runOsFactorSignPaper({ strategy_id: strategyId, instrument, bars: 400 }),
    onSuccess: () => notify("正式模拟已完成（无真实资金）", "success"),
    onError: (e) => notify(apiErrorMessage(e, "模拟失败"), "error"),
  });

  const shadow = useQuery({
    queryKey: ["os-shadow", strategyId, instrument, tab],
    queryFn: () => getOsShadow({ strategy_id: strategyId, instrument, bars: 120 }),
    enabled: tab === "shadow",
  });

  const governor = useQuery({
    queryKey: ["os-gov"],
    queryFn: getOsGovernor,
    enabled: tab === "governor",
  });

  const dna = useQuery({
    queryKey: ["os-dna", strategyId],
    queryFn: () => getOsDna(strategyId),
    enabled: tab === "dna",
  });

  const readiness = useQuery({
    queryKey: ["os-ready"],
    queryFn: getOsLiveReadiness,
    enabled: tab === "readiness",
  });

  const experiments = useQuery({
    queryKey: ["os-exps"],
    queryFn: () => listOsExperiments(40),
    enabled: tab === "experiments",
  });

  const expDetail = useQuery({
    queryKey: ["os-exp", selectedExp],
    queryFn: () => getOsExperiment(selectedExp!),
    enabled: Boolean(selectedExp),
  });

  const reproduce = useMutation({
    mutationFn: () => reproduceOsExperiment(selectedExp!),
    onSuccess: () => notify("已返回复现/核对结果", "success"),
    onError: (e) => notify(apiErrorMessage(e, "复现失败"), "error"),
  });

  const spec = useQuery({
    queryKey: ["os-spec", strategyId],
    queryFn: () => getOsStrategy(strategyId),
    enabled: tab === "spec",
  });

  const strategyOptions = useMemo(
    () => (strategies.data?.items || []).filter((x) => !x.error),
    [strategies.data],
  );

  return (
    <div className="pb-10">
      <PageTitle
        title="证据操作系统"
        subtitle="先证明，再下注 — 策略 → 实验 → 证据 → 晋级/暂缓/淘汰 → 模拟 → 影子 → 实盘资格"
      />

      <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 text-sm dark:border-emerald-900 dark:bg-emerald-950/30">
        <p className="font-semibold text-emerald-900 dark:text-emerald-100">产品教义：先证明，再下注</p>
        <p className="mt-1 text-emerald-800 dark:text-emerald-200">
          AI 创建策略只是研究工具。晋级不等于实盘。旧版 paper_orders / QMT / vn.py 下单路径已关闭。
        </p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <Link className="underline" to="/projects">
            研究项目
          </Link>
          <Link className="underline" to="/factor-scans">
            参数扫描（非账本）
          </Link>
          <Link className="underline" to="/ai-strategy">
            AI 研究工具
          </Link>
        </div>
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <label className="text-sm">
          <span className="mb-1 block text-slate-500">策略</span>
          <select
            className="input min-w-[16rem]"
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
          >
            {strategyOptions.map((s) => (
              <option key={String(s.strategy_id)} value={String(s.strategy_id)}>
                {String(s.strategy_id)} · {String(s.version)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-500">标的</span>
          <select className="input" value={instrument} onChange={(e) => setInstrument(e.target.value)}>
            <option value="RB">螺纹钢 RB</option>
            <option value="AU">黄金 AU</option>
            <option value="IF">股指 IF</option>
          </select>
        </label>
      </div>

      <div className="mb-4 min-w-0 max-w-full overflow-x-auto pb-1">
        <div className="flex w-max gap-1 px-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`shrink-0 rounded-lg px-3 py-2 text-sm font-medium ${
                tab === t.id
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
              }`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === "evidence" && (
        <section className="card space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold">证据流水线</h2>
              <p className="text-sm text-slate-500">样本外 · Walk-Forward · 压力 · 现实分 · 研究债 → 判定</p>
            </div>
            <button
              type="button"
              className="btn-primary"
              disabled={evidence.isPending}
              onClick={() => evidence.mutate()}
            >
              {evidence.isPending ? "判定中…" : "运行证据判定"}
            </button>
          </div>
          {evidence.isPending && <Spinner />}
          {evidence.data && <EvidenceCard data={evidence.data} />}
          {!evidence.data && !evidence.isPending && (
            <Empty hint="点击「运行证据判定」生成建议晋级 / 暂缓 / 淘汰，并解释为什么。" />
          )}
        </section>
      )}

      {tab === "spec" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">策略规格 Spec v2</h2>
          {spec.isLoading && <Spinner />}
          {spec.data && (
            <>
              <KV label="版本" value={`${spec.data.version}`} />
              <KV label="内容哈希" value={String(spec.data.lineage?.content_hash || "—")} />
              <KV
                label="谱系"
                value={`family=${spec.data.lineage?.family_id || "—"} · derived_from=${spec.data.lineage?.derived_from || "—"}`}
              />
              <p className="text-sm text-slate-600 dark:text-slate-300">
                合约 / 不变量 / 参数见下方只读 JSON（不修改策略结果）。
              </p>
              <pre className="max-h-80 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">
                {JSON.stringify(
                  {
                    lineage: spec.data.lineage,
                    contract: spec.data.contract,
                    invariants: spec.data.invariants,
                    parameters: spec.data.parameters,
                  },
                  null,
                  2,
                )}
              </pre>
              <DiffMini a={strategyId} />
            </>
          )}
        </section>
      )}

      {tab === "experiments" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">实验账本</h2>
          <p className="text-sm text-amber-800 dark:text-amber-200">
            {experiments.data?.not_factor_scan_zh || "本页不是参数扫描。"}
          </p>
          {experiments.isLoading && <Spinner />}
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {(experiments.data?.items || []).map((it: Record<string, unknown>) => (
              <li key={String(it.experiment_id)} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
                <div>
                  <div className="font-medium">{String(it.strategy_id)}</div>
                  <div className="text-slate-500">
                    {String(it.evidence_stage)} · 信任 {String(it.data_trust_status)} ·{" "}
                    {String(it.experiment_id).slice(0, 12)}…
                  </div>
                </div>
                <button type="button" className="btn text-xs" onClick={() => setSelectedExp(String(it.experiment_id))}>
                  查看
                </button>
              </li>
            ))}
          </ul>
          {!experiments.isLoading && !(experiments.data?.items || []).length && (
            <Empty hint="暂无封印实验。完成正式模拟后会写入账本。" />
          )}
          {selectedExp && expDetail.data && (
            <div className="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
              <h3 className="font-medium">实验详情</h3>
              <p className="mt-1 text-sm text-slate-600">{expDetail.data.explain_zh?.provenance_zh}</p>
              <p className="text-sm text-slate-600">{expDetail.data.explain_zh?.data_trust_zh}</p>
              <KV label="数据集哈希" value={String(expDetail.data.dataset_hash || "—")} />
              <button
                type="button"
                className="btn-primary mt-3 text-sm"
                disabled={reproduce.isPending}
                onClick={() => reproduce.mutate()}
              >
                {reproduce.isPending ? "复现中…" : "复现 / 核对"}
              </button>
              {reproduce.data && (
                <pre className="mt-3 max-h-48 overflow-auto rounded bg-slate-50 p-2 text-xs dark:bg-slate-900">
                  {JSON.stringify(reproduce.data, null, 2)}
                </pre>
              )}
            </div>
          )}
        </section>
      )}

      {tab === "paper" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">正式模拟 PaperRun</h2>
          <p className="text-sm text-slate-500">
            factor_sign → 正式适配器 → 模拟成交。禁止旧版 paper_orders。不涉及真实资金。
          </p>
          <button type="button" className="btn-primary" disabled={paper.isPending} onClick={() => paper.mutate()}>
            {paper.isPending ? "模拟中…" : "运行正式模拟"}
          </button>
          {paper.data && (
            <div className="space-y-2 text-sm">
              <p className="font-medium text-emerald-700 dark:text-emerald-300">{paper.data.explain_zh?.title_zh}</p>
              <p>{paper.data.explain_zh?.body_zh}</p>
              <KV label="语义一致性" value={String(paper.data.parity?.FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY)} />
              <KV label="成交笔数" value={String(paper.data.snapshot?.trade_count)} />
              <KV label="权益" value={String(paper.data.snapshot?.equity)} />
              <KV label="最大回撤" value={String(paper.data.snapshot?.max_drawdown)} />
              <p className="text-slate-500">{paper.data.explain_zh?.next_zh}</p>
              <Link to="/paper" className="btn text-sm">
                打开模拟交易页（含 BTC 演示通道说明）→
              </Link>
            </div>
          )}
        </section>
      )}

      {tab === "shadow" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">影子对照 / 飞行记录</h2>
          {shadow.isLoading && <Spinner />}
          {shadow.data && (
            <>
              <p>{shadow.data.explain_zh?.body_zh}</p>
              <KV label="对照柱数" value={String(shadow.data.bars)} />
              <KV label="分歧次数" value={String(shadow.data.divergences)} />
              <KV label="行为一致性" value={String(shadow.data.behavior_parity?.parity)} />
              <KV label="封印连续证据" value={String(shadow.data.sealed_continuous_evidence)} />
              <div className="space-y-2">
                {(shadow.data.flight_preview_zh || []).map((ev: Record<string, string>) => (
                  <div key={ev.event_id} className="rounded-lg border border-slate-100 p-3 text-sm dark:border-slate-800">
                    <div>{ev.saw_zh}</div>
                    <div className="text-slate-500">{ev.why_zh}</div>
                    <div className="text-slate-500">{ev.risk_zh}</div>
                    <div>{ev.happened_zh}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      )}

      {tab === "governor" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">组合治理</h2>
          {governor.isLoading && <Spinner />}
          {governor.data && (
            <>
              <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
                {governor.data.warning_zh}
              </p>
              <KV label="相关峰值 |ρ|" value={String(governor.data.correlation?.max_abs ?? "—")} />
              <pre className="max-h-40 overflow-auto rounded bg-slate-50 p-2 text-xs dark:bg-slate-900">
                {JSON.stringify(
                  { clusters: governor.data.clusters, capacity: governor.data.capacity, actions: governor.data.actions },
                  null,
                  2,
                )}
              </pre>
            </>
          )}
        </section>
      )}

      {tab === "dna" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">DNA / 谱系 / 坟场</h2>
          {dna.isLoading && <Spinner />}
          {dna.data && (
            <>
              <p>{dna.data.explain_zh?.body_zh}</p>
              <p className="text-sm text-slate-500">{dna.data.explain_zh?.no_edge_zh}</p>
              <pre className="max-h-64 overflow-auto rounded bg-slate-50 p-2 text-xs dark:bg-slate-900">
                {JSON.stringify(
                  {
                    dna: dna.data.dna,
                    memory_preview: dna.data.memory_preview,
                    graveyard_preview: dna.data.graveyard_preview,
                  },
                  null,
                  2,
                )}
              </pre>
            </>
          )}
        </section>
      )}

      {tab === "readiness" && (
        <section className="card space-y-3">
          <h2 className="text-lg font-semibold">实盘资格</h2>
          {readiness.isLoading && <Spinner />}
          {readiness.data && (
            <>
              <p className="text-xl font-bold text-rose-700 dark:text-rose-300">{readiness.data.headline_zh}</p>
              <KV label="工程资格" value={String(readiness.data.label_zh)} />
              <p className="text-sm">{readiness.data.caveat_zh}</p>
              <p className="text-sm font-medium">{readiness.data.broker_hold_zh}</p>
              <KV label="LIVE_READINESS" value={String(readiness.data.LIVE_READINESS)} />
              <KV label="券商能力" value={String(readiness.data.BROKER_LIVE_CAPABILITY)} />
              <ul className="list-disc pl-5 text-sm">
                {(readiness.data.owner_required_zh || []).map((x: string) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
              <p className="text-xs text-slate-500">
                QLN_11_STARTED={readiness.data.QLN_11_STARTED} · REAL_MONEY={readiness.data.REAL_MONEY}
              </p>
            </>
          )}
        </section>
      )}
    </div>
  );
}

function EvidenceCard({ data }: { data: Record<string, any> }) {
  const d = data.decision_zh || {};
  return (
    <div className="space-y-3">
      <div className="rounded-xl border-2 border-brand-300 bg-brand-50/50 p-4 dark:border-brand-800 dark:bg-brand-950/30">
        <p className="text-xs uppercase tracking-wide text-slate-500">当前结果</p>
        <p className="text-2xl font-bold">{d.label_zh}</p>
        <p className="mt-1 text-sm">{d.summary_zh}</p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">下一步：{d.next_zh}</p>
        <p className="mt-1 text-xs text-slate-500">{d.live_note_zh}</p>
      </div>
      <div>
        <h3 className="font-medium">为什么</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
          {(d.why_zh || []).map((r: string) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="font-medium">闸门</h3>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {Object.entries(data.gates_zh || {}).map(([k, v]: [string, any]) => (
            <div key={k} className="rounded-lg border border-slate-100 px-3 py-2 text-sm dark:border-slate-800">
              <div className="font-medium">{v.name_zh}</div>
              <div className="text-slate-500">{v.flag_zh}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 text-sm">
        <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-900">
          <div className="font-medium">现实分</div>
          <div>{data.reality_explain_zh?.score}</div>
          <p className="mt-1 text-xs text-slate-500">{data.reality_explain_zh?.why_zh}</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-900">
          <div className="font-medium">研究债</div>
          <div>{data.debt_explain_zh?.score}</div>
          <p className="mt-1 text-xs text-slate-500">{data.debt_explain_zh?.why_zh}</p>
        </div>
      </div>
    </div>
  );
}

function DiffMini({ a }: { a: string }) {
  const [b, setB] = useState("hist_fl_rsi_w14");
  const [out, setOut] = useState<Record<string, unknown> | null>(null);
  return (
    <div className="mt-3 rounded-lg border border-dashed border-slate-300 p-3 text-sm">
      <p className="font-medium">语义差异</p>
      <div className="mt-2 flex flex-wrap gap-2">
        <input className="input" value={b} onChange={(e) => setB(e.target.value)} />
        <button
          type="button"
          className="btn text-xs"
          onClick={async () => {
            try {
              setOut(await diffOsStrategies(a, b));
            } catch {
              setOut({ error: "diff failed" });
            }
          }}
        >
          对比
        </button>
      </div>
      {out && (
        <pre className="mt-2 max-h-40 overflow-auto text-xs">{JSON.stringify(out, null, 2)}</pre>
      )}
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-wrap gap-2 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="break-all font-medium">{value}</span>
    </div>
  );
}

function Empty({ hint }: { hint: string }) {
  return <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-900 dark:text-slate-300">{hint}</p>;
}

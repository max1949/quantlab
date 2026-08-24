import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { runAiStrategyBuilder } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";

type BuilderOut = {
  status?: string;
  live_denied?: boolean;
  paper_ready?: boolean;
  builder?: {
    ambiguous?: boolean;
    deployable?: boolean;
    confirmation_zh?: string[];
    questions?: { field: string; question_zh: string; assumed_value?: string | null }[];
    assumed_values?: string[];
    draft_spec?: {
      strategy?: { name?: string };
      market?: { instrument?: string; timeframe?: string };
      entry?: { long?: { conditions?: { type: string; params: Record<string, unknown> }[] } };
      stop_loss?: { type?: string; value?: number | null };
      take_profit?: { type?: string; value?: number | null };
      position_sizing?: { risk_per_trade?: number | null };
    };
  };
  data_gate_user?: { title_zh?: string; body_zh?: string; issues_zh?: string[] };
  report_zh?: {
    verdict_zh?: string;
    bullets_zh?: string[];
    next_step_zh?: string;
    disclaimer_zh?: string;
    terms_zh?: Record<string, string>;
  };
  status_card?: Record<string, string>;
  validation_gate?: { summary_zh?: string; lifecycle?: string; paper_ready?: boolean };
  dataset?: { available?: boolean; message_zh?: string; instrument?: string };
};

function ExplainTip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="ml-2 inline-block">
      <button
        type="button"
        className="text-xs text-brand-600 underline"
        onClick={() => setOpen((v) => !v)}
      >
        这是什么意思？
      </button>
      {open && (
        <span className="mt-1 block rounded-md bg-slate-50 p-2 text-xs text-slate-600 dark:bg-slate-900 dark:text-slate-300">
          {text}
        </span>
      )}
    </span>
  );
}

export default function AiCreateStrategy() {
  const notify = useUi((s) => s.notify);
  const [text, setText] = useState(
    "欧元美元15分钟。EMA20上穿EMA60。每笔最多亏0.5%。2倍ATR止损，4倍ATR止盈。"
  );
  const [result, setResult] = useState<BuilderOut | null>(null);

  const draft = useMutation({
    mutationFn: () => runAiStrategyBuilder({ text, confirm: false, run_backtest: false }),
    onSuccess: (data) => setResult(data),
    onError: (e) => notify(apiErrorMessage(e, "无法理解交易想法"), "error"),
  });

  const confirmRun = useMutation({
    mutationFn: () => runAiStrategyBuilder({ text, confirm: true, run_backtest: true }),
    onSuccess: (data) => {
      setResult(data);
      notify(data.status === "ok" ? "回测完成（仅研究，非实盘）" : "已返回结果", "success");
    },
    onError: (e) => notify(apiErrorMessage(e, "回测失败"), "error"),
  });

  const understood = useMemo(() => {
    const spec = result?.builder?.draft_spec;
    if (!spec) return null;
    const ema = spec.entry?.long?.conditions?.find((c) => c.type === "ema_cross")?.params;
    return {
      instrument: spec.market?.instrument || "—",
      timeframe: spec.market?.timeframe || "—",
      entry: ema ? `EMA${ema.fast} 上穿 EMA${ema.slow}` : "待确认",
      stop: spec.stop_loss?.type === "atr_mult" ? `${spec.stop_loss.value}倍ATR` : "未设置/假设无止损",
      take: spec.take_profit?.type === "atr_mult" ? `${spec.take_profit.value}倍ATR` : "未设置",
      risk:
        spec.position_sizing?.risk_per_trade != null
          ? `${(Number(spec.position_sizing.risk_per_trade) * 100).toFixed(2)}%`
          : "未设置",
    };
  }, [result]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">AI 创建策略</h1>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        告诉 AI 你的交易想法。系统会先结构化确认，再检查数据并回测。不会直接下真钱单。
      </p>

      <label className="mt-6 block text-sm font-medium text-slate-700 dark:text-slate-200">
        告诉 AI 你的交易想法
      </label>
      <textarea
        className="input mt-2 min-h-36 w-full text-sm"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="例如：黄金15分钟，EMA20上穿EMA60，每笔最多亏0.5%…"
      />

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="btn-primary text-sm"
          disabled={draft.isPending || !text.trim()}
          onClick={() => draft.mutate()}
        >
          {draft.isPending ? "理解中…" : "让 AI 理解规则"}
        </button>
        <button
          type="button"
          className="btn text-sm"
          disabled={confirmRun.isPending || !text.trim()}
          onClick={() => confirmRun.mutate()}
        >
          {confirmRun.isPending ? "回测中…" : "确认并回测"}
        </button>
      </div>

      {result?.builder?.questions && result.builder.questions.length > 0 && (
        <section className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950/40">
          <h2 className="font-medium text-amber-900 dark:text-amber-200">还需要确认</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900 dark:text-amber-100">
            {result.builder.questions.map((q) => (
              <li key={q.field + q.question_zh}>{q.question_zh}</li>
            ))}
          </ul>
        </section>
      )}

      {understood && (
        <section className="mt-6 rounded-xl border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="font-medium">我理解的策略</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700 dark:text-slate-200">
            <li>交易品种：{understood.instrument}</li>
            <li>周期：{understood.timeframe}</li>
            <li>做多：{understood.entry}</li>
            <li>
              止损：{understood.stop}
              <ExplainTip text="止损是单笔亏损达到预设水平时自动离场，用来限制最坏情况。" />
            </li>
            <li>止盈：{understood.take}</li>
            <li>
              单笔最大风险：{understood.risk}
              <ExplainTip text="意思是如果这笔交易失败，你愿意最多亏账户的多少比例。" />
            </li>
          </ul>
          {result?.builder?.assumed_values && result.builder.assumed_values.length > 0 && (
            <p className="mt-3 text-xs text-slate-500">
              含假设值（ASSUMED_VALUE）：{result.builder.assumed_values.join("；")}
            </p>
          )}
          <p className="mt-2 text-xs text-slate-500">环境：仅研究回测 · LIVE 已拒绝 · 模拟运行未开启</p>
        </section>
      )}

      {result?.data_gate_user && (
        <section className="mt-6 rounded-xl border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="font-medium">{result.data_gate_user.title_zh}</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{result.data_gate_user.body_zh}</p>
          <ul className="mt-2 list-disc pl-5 text-sm">
            {(result.data_gate_user.issues_zh || []).map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </section>
      )}

      {result?.status_card && (
        <section className="mt-6 rounded-xl border border-brand-200 bg-brand-50/60 p-4 dark:border-brand-900 dark:bg-brand-950/30">
          <h2 className="text-lg font-semibold">{result.status_card.name}</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>{result.status_card.research_status_zh}</p>
            <p>{result.status_card.robustness_zh}</p>
            <p>{result.status_card.data_quality_zh}</p>
            <p>
              {result.status_card.max_drawdown_zh}
              <ExplainTip text="意思是历史最差阶段，账户曾从高点下跌这么多。若账户 10 万美元，12.4% 约等于曾下降 1.24 万美元。" />
            </p>
            <p>{result.status_card.enter_simulation_zh}</p>
            <p className="pt-2 font-medium">AI结论：{result.status_card.ai_conclusion_zh}</p>
          </div>
        </section>
      )}

      {result?.report_zh && (
        <section className="mt-6 rounded-xl border border-slate-200 p-4 dark:border-slate-700">
          <h2 className="font-medium">中文回测解释</h2>
          <p className="mt-2 text-sm">{result.report_zh.verdict_zh}</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-200">
            {(result.report_zh.bullets_zh || []).map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          <p className="mt-2 text-sm text-slate-600">{result.report_zh.next_step_zh}</p>
          <p className="mt-3 text-xs text-slate-500">{result.report_zh.disclaimer_zh}</p>
        </section>
      )}

      {result?.dataset && result.dataset.available === false && (
        <section className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm dark:border-rose-900 dark:bg-rose-950/40">
          {result.dataset.message_zh}
        </section>
      )}
    </div>
  );
}

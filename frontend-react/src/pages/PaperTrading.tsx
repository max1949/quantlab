import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { runOsFactorSignPaper, listOsStrategies } from "../api/researchOs";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { apiErrorMessage } from "../api/client";
import { useState } from "react";

/**
 * Canonical Paper Trading page.
 * BTC EMA sandbox bootstrap was retired — it 500'd / confused users after PaperRun closure.
 * Only factor_sign → PaperRuntimeContract path remains as primary action.
 */
export default function PaperTrading() {
  const notify = useUi((s) => s.notify);
  const t = useLocale((s) => s.dict);
  const [params] = useSearchParams();
  const [strategyId, setStrategyId] = useState(params.get("strategy") || "hist_fl_momentum_w20");
  const [instrument, setInstrument] = useState(params.get("instrument") || "RB");
  const [fsResult, setFsResult] = useState<Record<string, unknown> | null>(null);
  const [showRetiredNote, setShowRetiredNote] = useState(false);

  const strategies = useQuery({ queryKey: ["os-strategies"], queryFn: listOsStrategies });

  const factorSign = useMutation({
    mutationFn: () => runOsFactorSignPaper({ strategy_id: strategyId, instrument, bars: 400 }),
    onSuccess: (data) => {
      setFsResult(data);
      notify("正式模拟完成（不涉及真实资金）", "success");
    },
    onError: (e) => notify(apiErrorMessage(e, "正式模拟未能完成，请稍后重试或先打开证据系统"), "error"),
  });

  const opts = (strategies.data?.items || []).filter((x) => !x.error);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 rounded-xl border-2 border-amber-400 bg-amber-50 p-4 text-center dark:border-amber-600 dark:bg-amber-950/40">
        <p className="text-2xl font-bold text-amber-900 dark:text-amber-100">模拟交易，不涉及真实资金</p>
        <p className="mt-1 text-sm text-amber-800 dark:text-amber-200">
          正式路径：策略规格 → factor_sign 适配器 → PaperRun。旧版 paper_orders / BTC 演示沙盒已关闭。实盘未开放。
        </p>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">{t.nav?.paperTrading || "模拟交易"}</h1>
        <Link to="/evidence" className="btn text-sm">
          先去证据判定 →
        </Link>
      </div>

      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900/40">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          选择策略规格，运行 canonical 正式模拟。用于挑战「正式模拟成交」里程碑与观察净值，不是实盘。
        </p>
        {strategies.isError ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-100">
            无法加载策略列表：{apiErrorMessage(strategies.error)}。请确认已登录，或稍后重试。
          </div>
        ) : null}
        <div className="flex flex-wrap gap-3">
          <select
            className="input min-w-[12rem]"
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            disabled={factorSign.isPending}
          >
            {opts.length === 0 ? <option value={strategyId}>{strategyId}</option> : null}
            {opts.map((s) => (
              <option key={String(s.strategy_id)} value={String(s.strategy_id)}>
                {String(s.strategy_id)}
              </option>
            ))}
          </select>
          <select
            className="input"
            value={instrument}
            onChange={(e) => setInstrument(e.target.value)}
            disabled={factorSign.isPending}
          >
            <option value="RB">螺纹钢 RB</option>
            <option value="AU">黄金 AU</option>
            <option value="IF">股指 IF</option>
          </select>
          <button
            type="button"
            className="btn-primary"
            disabled={factorSign.isPending}
            onClick={() => factorSign.mutate()}
          >
            {factorSign.isPending ? "模拟中…" : "运行正式模拟"}
          </button>
        </div>

        {factorSign.isError ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-100">
            {apiErrorMessage(factorSign.error, "正式模拟失败")}
            <p className="mt-1 text-xs">建议：打开证据系统确认策略规格，或更换标的后重试。不会创建真实订单。</p>
          </div>
        ) : null}

        {fsResult && (
          <div className="space-y-2 text-sm">
            <div>
              运行时：{String((fsResult as { PAPER_RUNTIME?: string }).PAPER_RUNTIME)} · 旧路径：
              {String((fsResult as { LEGACY_PAPER_ORDERS_USED?: string }).LEGACY_PAPER_ORDERS_USED)}
            </div>
            <div>
              语义一致性：
              {String(
                (fsResult as { parity?: { FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY?: string } }).parity
                  ?.FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY,
              )}
            </div>
            <div>
              成交：{String((fsResult as { snapshot?: { trade_count?: number } }).snapshot?.trade_count)} · 权益：
              {String((fsResult as { snapshot?: { equity?: number } }).snapshot?.equity)}
            </div>
            <p className="text-slate-500">
              {String(
                (fsResult as { explain_zh?: { next_zh?: string } }).explain_zh?.next_zh ||
                  "可返回挑战查看进度，或打开影子对照。",
              )}
            </p>
            <div className="flex flex-wrap gap-2">
              <Link to="/challenges" className="btn text-sm">
                返回挑战 →
              </Link>
              <Link to="/evidence" className="btn text-sm">
                证据 / 影子对照 →
              </Link>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 rounded-xl border border-dashed border-slate-300 p-4 text-sm dark:border-slate-600">
        <button
          type="button"
          className="font-medium text-slate-700 underline dark:text-slate-200"
          onClick={() => setShowRetiredNote((v) => !v)}
        >
          {showRetiredNote ? "收起" : "为什么没有「启动 BTC 模拟」？"}
        </button>
        {showRetiredNote ? (
          <div className="mt-2 space-y-2 text-slate-600 dark:text-slate-300">
            <p>
              旧的「启动 BTC 模拟」走的是硬编码 EMA 沙盒演示，在正式 PaperRun 收口后容易触发服务器错误，且不能代表你的策略晋级路径。
            </p>
            <p>
              该入口已退役。请使用上方「运行正式模拟」。旧版 paper_orders / QMT / vn.py 新单同样已关闭。
            </p>
            <p className="text-xs text-slate-500">REAL_MONEY=NO · LEGACY_PAPER_PATH_REINTRODUCED=NO</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

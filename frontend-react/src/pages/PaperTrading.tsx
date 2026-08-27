import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getPaperSandboxDashboard,
  startPaperRun,
  stopPaperRun,
  killPaperRun,
  createPaperSandboxRun,
  registerPaperReady,
} from "../api/endpoints";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { apiErrorMessage } from "../api/client";

export default function PaperTrading() {
  const notify = useUi((s) => s.notify);
  const t = useLocale((s) => s.dict);
  const qc = useQueryClient();

  const demoRunId = sessionStorage.getItem("paper_run_id") || "";

  const dashboard = useQuery({
    queryKey: ["paper-dashboard", demoRunId],
    queryFn: () => getPaperSandboxDashboard(demoRunId),
    enabled: Boolean(demoRunId),
    refetchInterval: (q) => {
      const status = String((q.state.data as { status?: string } | undefined)?.status || "").toUpperCase();
      if (status === "RUNNING" || status === "STARTING") return 3000;
      return false;
    },
  });

  const bootstrap = useMutation({
    mutationFn: async () => {
      await registerPaperReady();
      const run = await createPaperSandboxRun();
      await startPaperRun(run.id);
      sessionStorage.setItem("paper_run_id", run.id);
      return run.id;
    },
    onSuccess: () => {
      notify("模拟交易已启动（不涉及真钱）", "success");
      void qc.invalidateQueries({ queryKey: ["paper-dashboard"] });
    },
    onError: (e) => notify(apiErrorMessage(e, "启动失败"), "error"),
  });

  const stopMut = useMutation({
    mutationFn: () => stopPaperRun(demoRunId),
    onSuccess: () => {
      notify("已请求优雅停止", "success");
      void dashboard.refetch();
    },
    onError: (e) => notify(apiErrorMessage(e, "停止失败"), "error"),
  });

  const killMut = useMutation({
    mutationFn: () => killPaperRun(demoRunId),
    onSuccess: () => {
      notify("已强制终止模拟（Kill Switch）", "info");
      void dashboard.refetch();
    },
    onError: (e) => notify(apiErrorMessage(e, "终止失败"), "error"),
  });

  const d = dashboard.data;
  const statusUpper = String(d?.status || "").toUpperCase();
  const isActive = statusUpper === "RUNNING" || statusUpper === "STARTING";

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 rounded-xl border-2 border-amber-400 bg-amber-50 p-4 text-center dark:border-amber-600 dark:bg-amber-950/40">
        <p className="text-2xl font-bold text-amber-900 dark:text-amber-100">模拟交易，不涉及真实资金</p>
        <p className="mt-1 text-sm text-amber-800 dark:text-amber-200">SANDBOX · Nautilus 模拟执行 · BTCUSDT · 实盘未开放</p>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">{t.nav?.paperTrading || "模拟交易"}</h1>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-primary" disabled={bootstrap.isPending} onClick={() => bootstrap.mutate()}>
            {bootstrap.isPending ? "启动中…" : demoRunId ? "重新启动 BTC 模拟" : "启动 BTC 模拟"}
          </button>
          {demoRunId && isActive ? (
            <>
              <button
                type="button"
                className="btn text-sm"
                disabled={stopMut.isPending}
                onClick={() => stopMut.mutate()}
              >
                {stopMut.isPending ? "停止中…" : "停止"}
              </button>
              <button
                type="button"
                className="btn text-sm text-rose-700"
                disabled={killMut.isPending}
                onClick={() => killMut.mutate()}
              >
                {killMut.isPending ? "终止中…" : "强制终止"}
              </button>
            </>
          ) : null}
        </div>
      </div>

      {dashboard.isError ? (
        <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-100">
          无法读取模拟状态：{apiErrorMessage(dashboard.error)}。可尝试重新启动，或检查登录是否过期。
        </div>
      ) : null}

      {d ? (
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900/40">
          <div className="text-lg font-medium">{d.strategy_name} · {d.strategy_version}</div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Stat label="状态" value={d.status_zh || d.status || "—"} />
            <Stat label="运行时间" value={d.uptime_zh} />
            <Stat label="权益 (Equity)" value={d.equity_zh || d.simulated_balance_zh} />
            <Stat label="累计盈亏" value={d.total_pnl_zh} />
            <Stat label="未实现盈亏" value={d.unrealized_pnl_zh || "—"} />
            <Stat label="最大回撤" value={d.max_drawdown_zh || "—"} />
            <Stat label="当前持仓" value={d.position_zh} />
            <Stat label="当前风险" value={d.risk_zh} />
            <Stat label="数据源" value={d.data_provider || "synthetic"} />
            <Stat label="数据连接" value={d.data_connection_zh} />
          </div>
          {d.parity_status ? (
            <div className="text-sm text-slate-600 dark:text-slate-300">
              回测/模拟一致性：<span className="font-medium">{d.parity_status}</span>
            </div>
          ) : null}
          <div className="text-sm text-slate-500">异常：{d.alert_count}</div>
          {d.orders_zh?.length ? (
            <div>
              <h3 className="mb-2 font-medium">最近订单</h3>
              <ul className="space-y-2 text-sm">
                {d.orders_zh.map((o: { label_zh: string; price: string; quantity: string; trigger_reason: string }, i: number) => (
                  <li key={i} className="rounded-lg border border-slate-100 p-3 dark:border-slate-800">
                    <div className="font-medium">{o.label_zh}</div>
                    <div className="text-slate-500">价格：{o.price} · 数量：{o.quantity}</div>
                    <div className="text-slate-500">触发原因：{o.trigger_reason}</div>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {Array.isArray(d.research_feedback_zh) && d.research_feedback_zh.length > 0 ? (
            <div>
              <h3 className="mb-2 font-medium">研究反馈</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
                {d.research_feedback_zh.map((line: string, i: number) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {Array.isArray(d.backtest_vs_paper_zh) && d.backtest_vs_paper_zh.length > 0 ? (
            <div>
              <h3 className="mb-2 font-medium">回测 vs 模拟</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
                {d.backtest_vs_paper_zh.map((line: string, i: number) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="text-slate-500">点击「启动 BTC 模拟」开始纸面沙盒体验。这是模拟盘，不会连接真实交易所账户。</p>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/50">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-base font-medium">{value}</div>
    </div>
  );
}

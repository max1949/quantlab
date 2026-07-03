import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  checkExecutionRisk,
  getExecutionConfig,
  listPaperOrders,
  submitPaperOrder,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import type { Dictionary } from "../i18n/dictionaries";

const SYMBOLS = ["RB", "AU", "IF"];
type ExecChannel = "paper" | "vnpy" | "qmt";

function isGatewayChannel(channel: ExecChannel): boolean {
  return channel === "vnpy" || channel === "qmt";
}

export default function PaperExecutionPanel() {
  const l4 = useLocale((s) => s.dict.l4Tools);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();

  const [symbol, setSymbol] = useState("RB");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [notional, setNotional] = useState("50000");
  const [channel, setChannel] = useState<ExecChannel>("paper");
  const [riskMsg, setRiskMsg] = useState("");

  const config = useQuery({ queryKey: ["execution-config"], queryFn: getExecutionConfig });
  const orders = useQuery({ queryKey: ["paper-orders"], queryFn: () => listPaperOrders(10) });

  const riskCheck = useMutation({
    mutationFn: () =>
      checkExecutionRisk({
        symbol,
        notional_cny: Number(notional),
        channel,
        acknowledge_risk: isGatewayChannel(channel),
      }),
    onSuccess: (r) => {
      setRiskMsg(r.message);
      notify(r.message, r.allowed ? "success" : "info");
    },
    onError: (e) => notify(apiErrorMessage(e, l4.execRiskFail), "error"),
  });

  const submit = useMutation({
    mutationFn: () =>
      submitPaperOrder({
        symbol,
        side,
        notional_cny: Number(notional),
        channel,
        acknowledge_risk: isGatewayChannel(channel),
      }),
    onSuccess: (o) => {
      notify(l4.execSubmitted(o.channel, o.status), "success");
      void qc.invalidateQueries({ queryKey: ["paper-orders"] });
    },
    onError: (e) => notify(apiErrorMessage(e, l4.execSubmitFail), "error"),
  });

  if (config.data?.kill_switch) {
    return (
      <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
        {l4.execKillSwitch}
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900/40">
      <h4 className="font-medium">{l4.execTitle}</h4>
      <p className="mb-3 text-sm text-slate-500">{l4.execDesc}</p>

      <div className="mb-3 flex flex-wrap gap-2">
        <select className="input text-sm" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
          {SYMBOLS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select className="input text-sm" value={side} onChange={(e) => setSide(e.target.value as "buy" | "sell")}>
          <option value="buy">{l4.execBuy}</option>
          <option value="sell">{l4.execSell}</option>
        </select>
        <select
          className="input text-sm"
          value={channel}
          onChange={(e) => setChannel(e.target.value as ExecChannel)}
        >
          <option value="paper">{l4.execChannelPaper}</option>
          <option value="vnpy">{l4.execChannelVnpy}</option>
          <option value="qmt">{l4.execChannelQmt}</option>
        </select>
        <input
          className="input w-32 text-sm"
          type="number"
          min={1000}
          value={notional}
          onChange={(e) => setNotional(e.target.value)}
          placeholder={l4.execNotional}
        />
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="btn text-sm"
          disabled={riskCheck.isPending}
          onClick={() => riskCheck.mutate()}
        >
          {riskCheck.isPending ? l4.execChecking : l4.execRiskBtn}
        </button>
        <button
          type="button"
          className="btn-primary text-sm"
          disabled={submit.isPending || !notional}
          onClick={() => submit.mutate()}
        >
          {submit.isPending ? l4.execSubmitting : l4.execSubmitBtn}
        </button>
      </div>

      {riskMsg && <p className="mb-3 text-xs text-slate-500">{riskMsg}</p>}

      {orders.data && orders.data.length > 0 && (
        <OrderList rows={orders.data} l4={l4} />
      )}
    </div>
  );
}

function OrderList({ rows, l4 }: { rows: import("../api/types").PaperOrder[]; l4: Dictionary["l4Tools"] }) {
  return (
    <div className="text-xs text-slate-600 dark:text-slate-300">
      <p className="mb-1 font-medium">{l4.execRecent}</p>
      <ul className="space-y-1">
        {rows.slice(0, 5).map((o) => (
          <li key={o.id} className="font-mono">
            {o.symbol} {o.side} ¥{o.notional_cny.toLocaleString()} · {o.channel} · {o.status}
            {o.gateway_status ? ` (${o.gateway_status})` : ""}
            {o.external_ref ? ` · ${o.external_ref}` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  checkout,
  downloadBillingHistoryCsv,
  downloadBillingInvoicePdf,
  getBillingHistory,
  getEntitlements,
  getPlans,
  getSubscription,
  redeemCode,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Pricing() {
  const user = useAuth((s) => s.user);
  const notify = useUi((s) => s.notify);
  const p = useLocale((s) => s.dict.pricing);
  const qc = useQueryClient();

  const plans = useQuery({ queryKey: ["plans"], queryFn: getPlans });
  const sub = useQuery({
    queryKey: ["subscription"],
    queryFn: getSubscription,
    enabled: !!user,
  });
  const ent = useQuery({
    queryKey: ["entitlements"],
    queryFn: getEntitlements,
    enabled: !!user,
  });
  const billingHistory = useQuery({
    queryKey: ["billing-history"],
    queryFn: () => getBillingHistory(),
    enabled: !!user,
  });

  const [code, setCode] = useState("");
  const [billingExporting, setBillingExporting] = useState(false);

  const doRedeem = useMutation({
    mutationFn: () => redeemCode(code.trim()),
    onSuccess: (r) => {
      notify(r.message, "success");
      setCode("");
      void qc.invalidateQueries({ queryKey: ["subscription"] });
      void qc.invalidateQueries({ queryKey: ["entitlements"] });
      void qc.invalidateQueries({ queryKey: ["billing-history"] });
    },
    onError: (e) => notify(apiErrorMessage(e, p.redeemFailed), "error"),
  });

  const doCheckout = useMutation({
    mutationFn: (planCode: string) => checkout(planCode),
    onSuccess: (r) => {
      if (r.configured && r.pay_url) {
        window.location.href = r.pay_url;
        return;
      }
      notify(r.message, r.configured ? "success" : "info");
    },
    onError: (e) => notify(apiErrorMessage(e, p.redeemFailed), "error"),
  });

  if (plans.isLoading) return <Spinner />;
  if (plans.isError || !plans.data) return <ErrorBox message={p.loadFailed} />;

  const currentTier = sub.data?.tier ?? 0;
  const personalPlans = plans.data.filter((plan) => plan.kind !== "org");
  const orgPlans = plans.data.filter((plan) => plan.kind === "org");

  return (
    <div>
      <PageTitle title={p.title} subtitle={p.subtitle} />

      {user && sub.data && (
        <div className="mb-6 rounded-xl border border-brand-100 bg-brand-50/50 px-4 py-3 text-sm dark:border-brand-900 dark:bg-brand-950/40">
          {p.current}:{" "}
          <b>
            {user.level_label} · {sub.data.tier_name} {p.member}
          </b>
          {sub.data.expires_at && (
            <span className="text-slate-500">
              {" "}
              ({p.expires}{" "}
              {new Date(sub.data.expires_at).toLocaleDateString()})
            </span>
          )}
          {sub.data.org_benefit && (
            <div className="mt-1 text-slate-600 dark:text-slate-400">{p.orgBenefit}</div>
          )}
          {ent.data?.market_data?.summary && (
            <div className="mt-1 text-slate-600 dark:text-slate-400">
              {p.dataPlan}: {ent.data.market_data.summary}
            </div>
          )}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        {personalPlans.map((plan) => {
          const isCurrent = currentTier === plan.tier;
          const isFree = plan.tier === 0;
          return (
            <div
              key={plan.code}
              className={`card flex flex-col ${
                plan.tier === 1 ? "border-brand-300 ring-1 ring-brand-200 dark:border-brand-700" : ""
              }`}
            >
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                {plan.tier === 1 && <span className="badge">{p.popular}</span>}
              </div>
              <p className="mb-3 text-sm text-slate-500">{plan.tagline}</p>
              <div className="mb-4">
                <span className="text-3xl font-bold">¥{plan.price_cny}</span>
                {!isFree && <span className="text-slate-400">{p.perMonth}</span>}
              </div>
              <ul className="mb-4 flex-1 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <span className="text-brand-600">✓</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              {isFree ? (
                <button className="btn-ghost w-full" disabled>
                  {isCurrent ? p.currentPlan : p.basicPlan}
                </button>
              ) : isCurrent ? (
                <button className="btn-ghost w-full" disabled>
                  {p.activePlan}
                </button>
              ) : (
                <button
                  className="btn-primary w-full"
                  disabled={doCheckout.isPending}
                  onClick={() => doCheckout.mutate(plan.code)}
                >
                  {p.buyWithCard}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {orgPlans.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-2 text-lg font-semibold">{p.teamTitle}</h2>
          <p className="mb-4 text-sm text-slate-500">{p.teamHint}</p>
          <div className="grid gap-4 md:grid-cols-2">
            {orgPlans.map((plan) => (
              <div key={plan.code} className="card flex flex-col">
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <p className="mb-2 text-sm text-slate-500">{plan.tagline}</p>
                <div className="mb-3">
                  <span className="text-2xl font-bold">¥{plan.price_cny}</span>
                  <span className="text-slate-400">{p.perMonth}</span>
                </div>
                <ul className="mb-4 flex-1 space-y-1 text-sm text-slate-600 dark:text-slate-300">
                  {plan.features.map((f) => (
                    <li key={f}>✓ {f}</li>
                  ))}
                </ul>
                <Link to="/orgs" className="btn-primary w-full text-center">
                  {p.teamCta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {user && (
        <div className="mt-8 max-w-md">
          <h3 className="mb-2 font-semibold">{p.cardTitle}</h3>
          <p className="mb-3 text-sm text-slate-500">{p.cardHint}</p>
          <div className="flex gap-2">
            <input
              className="input font-mono"
              placeholder="BKTA-XXXX-XXXX"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <button
              className="btn-primary whitespace-nowrap"
              disabled={doRedeem.isPending || !code.trim()}
              onClick={() => doRedeem.mutate()}
            >
              {doRedeem.isPending ? p.redeeming : p.redeem}
            </button>
          </div>
        </div>
      )}

      {user && billingHistory.data && billingHistory.data.length > 0 && (
        <div className="mt-8 card max-w-2xl">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold">{p.billingHistoryTitle}</h3>
            <button
              type="button"
              className="btn text-xs"
              disabled={billingExporting}
              onClick={() => {
                setBillingExporting(true);
                void downloadBillingHistoryCsv()
                  .catch((e) => notify(apiErrorMessage(e, p.billingExportFail), "error"))
                  .finally(() => setBillingExporting(false));
              }}
            >
              {billingExporting ? p.billingExporting : p.billingExportCsv}
            </button>
          </div>
          <ul className="space-y-2 text-sm">
            {billingHistory.data.slice(0, 10).map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 py-2 dark:border-slate-800"
              >
                <span>
                  {row.plan_name} · {row.tier_name}
                </span>
                <span className="text-slate-400">
                  ¥{row.amount_cny.toLocaleString()} · {row.source} ·{" "}
                  {new Date(row.created_at).toLocaleDateString()}
                </span>
                <button
                  type="button"
                  className="btn text-xs"
                  onClick={() =>
                    void downloadBillingInvoicePdf(row.id).catch((e) =>
                      notify(apiErrorMessage(e, p.invoiceDownloadFail), "error"),
                    )
                  }
                >
                  {p.invoicePdf}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!user && (
        <p className="mt-8 text-sm text-slate-500">{p.loginFirst}</p>
      )}
    </div>
  );
}

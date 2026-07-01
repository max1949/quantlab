import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  checkout,
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

  const [code, setCode] = useState("");

  const doRedeem = useMutation({
    mutationFn: () => redeemCode(code.trim()),
    onSuccess: (r) => {
      notify(r.message, "success");
      setCode("");
      void qc.invalidateQueries({ queryKey: ["subscription"] });
      void qc.invalidateQueries({ queryKey: ["entitlements"] });
    },
    onError: (e) => notify(apiErrorMessage(e, p.redeemFailed), "error"),
  });

  const doCheckout = useMutation({
    mutationFn: (planCode: string) => checkout(planCode),
    onSuccess: (r) => notify(r.message, r.configured ? "success" : "info"),
    onError: (e) => notify(apiErrorMessage(e, p.redeemFailed), "error"),
  });

  if (plans.isLoading) return <Spinner />;
  if (plans.isError || !plans.data) return <ErrorBox message={p.loadFailed} />;

  const currentTier = sub.data?.tier ?? 0;

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
          {ent.data?.market_data?.summary && (
            <div className="mt-1 text-slate-600 dark:text-slate-400">
              {p.dataPlan}: {ent.data.market_data.summary}
            </div>
          )}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        {plans.data.map((plan) => {
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

      {!user && (
        <p className="mt-8 text-sm text-slate-500">{p.loginFirst}</p>
      )}
    </div>
  );
}

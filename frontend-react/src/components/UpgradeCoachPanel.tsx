import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { checkout, getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

export default function UpgradeCoachPanel() {
  const u = useLocale((s) => s.dict.upgradeCoach);
  const notify = useUi((s) => s.notify);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const coach = journey.data?.upgrade_coaching;
  const doCheckout = useMutation({
    mutationFn: () => checkout(coach!.plan_code),
    onSuccess: (r) => {
      if (r.configured && r.pay_url) {
        window.location.href = r.pay_url;
        return;
      }
      notify(r.message, r.configured ? "success" : "info");
    },
  });

  if (!coach) return null;

  return (
    <div className="card border border-indigo-200 bg-gradient-to-r from-indigo-50/80 to-brand-50/50 dark:border-indigo-900 dark:from-indigo-950/30 dark:to-brand-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700 dark:text-indigo-300">
            {u.badge(coach.target_tier_name)}
          </p>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{coach.message}</p>
          <p className="mt-2 text-xs text-slate-500">
            {u.unlock(coach.unlock_features)} · {u.planPrice(coach.plan_name, coach.price_cny)}
          </p>
          {!coach.stripe_available && (
            <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">{u.redeemHint}</p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {coach.stripe_available ? (
            <button
              type="button"
              className="btn-primary whitespace-nowrap text-xs"
              disabled={doCheckout.isPending}
              onClick={() => doCheckout.mutate()}
            >
              {u.checkoutCta}
            </button>
          ) : (
            <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs">
              {u.viewPlans}
            </Link>
          )}
          <Link to={coach.cta_path} className="btn whitespace-nowrap text-xs">
            {u.viewPlans}
          </Link>
        </div>
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { checkout, getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

export default function MarketDataCoachPanel() {
  const d = useLocale((s) => s.dict.marketDataCoach);
  const notify = useUi((s) => s.notify);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: getResearchJourney });

  const coach = journey.data?.market_data_coaching;
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
    <div className="card border border-sky-200 bg-gradient-to-r from-sky-50/80 to-cyan-50/40 dark:border-sky-900 dark:from-sky-950/30 dark:to-cyan-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-300">
            {d.badge(coach.symbol, coach.timeframe)}
          </p>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{coach.message}</p>
          <p className="mt-2 text-xs text-slate-500">
            {d.currentPlan(coach.current_summary)} → {d.targetPlan(coach.target_summary)}
          </p>
          {coach.effective_rows != null && coach.total_rows != null && (
            <p className="mt-1 text-xs text-sky-800/90 dark:text-sky-200/90">
              {d.barsUsed(coach.effective_rows, coach.total_rows)}
            </p>
          )}
          {coach.quality_warnings.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-xs text-amber-800 dark:text-amber-200">
              {coach.quality_warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
          {!coach.stripe_available && (
            <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">{d.redeemHint}</p>
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
              {d.upgradeCta(coach.plan_name, coach.price_cny)}
            </button>
          ) : (
            <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs">
              {d.viewPlans}
            </Link>
          )}
          <Link to={coach.cta_path} className="btn whitespace-nowrap text-xs">
            {d.viewPlans}
          </Link>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { stageToCtaLabel } from "../lib/nav";

export default function PostCheckoutCoachPanel() {
  const d = useLocale((s) => s.dict.postCheckoutCoach);
  const stages = useLocale((s) => s.dict.stages);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const checkoutPlan =
    searchParams.get("checkout") === "success" ? searchParams.get("plan") : null;

  const notified = useRef(false);

  const journey = useQuery({
    queryKey: ["research-journey", checkoutPlan],
    queryFn: () => getResearchJourney({ checkoutPlan: checkoutPlan ?? undefined }),
    enabled: !!checkoutPlan,
    refetchInterval: (query) =>
      query.state.data?.checkout_coaching || query.state.fetchFailureCount >= 3 ? false : 2000,
  });

  useEffect(() => {
    if (!checkoutPlan || notified.current) return;
    notified.current = true;
    notify(d.successToast, "success");
    void qc.invalidateQueries({ queryKey: ["subscription"] });
    void qc.invalidateQueries({ queryKey: ["entitlements"] });
    void qc.invalidateQueries({ queryKey: ["billing-history"] });
    void qc.invalidateQueries({ queryKey: ["next-step"] });
  }, [checkoutPlan, d.successToast, notify, qc]);

  const coach = journey.data?.checkout_coaching;
  if (!coach) return null;

  const ctaLabel =
    coach.cta_action in stages
      ? stageToCtaLabel(coach.cta_action, stages)
      : d.ctaDefault;

  const dismiss = () => {
    searchParams.delete("checkout");
    searchParams.delete("plan");
    setSearchParams(searchParams, { replace: true });
  };

  return (
    <div className="card border border-emerald-200 bg-gradient-to-r from-emerald-50/90 to-teal-50/50 dark:border-emerald-900 dark:from-emerald-950/40 dark:to-teal-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
            {d.badge(coach.tier_name, coach.plan_name)}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{coach.message}</p>
          <p className="mt-2 text-xs text-emerald-800/90 dark:text-emerald-200/90">
            {d.unlocked(coach.unlock_features)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to={coach.cta_path} className="btn-primary whitespace-nowrap text-xs">
            {ctaLabel}
          </Link>
          <Link to="/pricing" className="btn whitespace-nowrap text-xs">
            {d.viewPlans}
          </Link>
          <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        </div>
      </div>
    </div>
  );
}

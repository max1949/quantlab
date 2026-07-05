import { useEffect } from "react";
import { Link } from "react-router-dom";
import { burstConfetti } from "../lib/confetti";
import { FIRST_FOLLOWING_FEED_WELCOME_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

export default function FollowingFeedWelcomePanel() {
  const d = useLocale((s) => s.dict.followingFeedWelcome);
  const show =
    typeof window !== "undefined" && sessionStorage.getItem(FIRST_FOLLOWING_FEED_WELCOME_KEY) === "1";

  useEffect(() => {
    if (!show) return;
    sessionStorage.removeItem(FIRST_FOLLOWING_FEED_WELCOME_KEY);
    burstConfetti(2800);
  }, [show]);

  if (!show) return null;

  return (
    <div className="mb-4 card border border-emerald-200 bg-gradient-to-r from-emerald-50/90 to-teal-50/60 dark:border-emerald-900 dark:from-emerald-950/40 dark:to-teal-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
        🎉 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <p className="mt-2 text-xs text-emerald-800/90 dark:text-emerald-100/90">{d.hint}</p>
      <Link to="#following-feed-grid" className="btn-primary mt-3 inline-block text-xs">
        {d.scrollReports}
      </Link>
    </div>
  );
}

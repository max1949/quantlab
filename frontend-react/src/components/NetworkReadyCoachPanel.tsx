import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FIRST_FOLLOWING_FEED_WELCOME_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

export default function NetworkReadyCoachPanel() {
  const d = useLocale((s) => s.dict.networkReadyCoach);
  const [pending, setPending] = useState(
    () => typeof window !== "undefined" && sessionStorage.getItem(FIRST_FOLLOWING_FEED_WELCOME_KEY) === "1",
  );

  useEffect(() => {
    const sync = () => {
      setPending(sessionStorage.getItem(FIRST_FOLLOWING_FEED_WELCOME_KEY) === "1");
    };
    window.addEventListener("quantlab-network-milestone", sync);
    return () => window.removeEventListener("quantlab-network-milestone", sync);
  }, []);

  if (!pending) return null;

  return (
    <div className="mb-4 card border border-emerald-300 bg-gradient-to-r from-emerald-50/95 to-cyan-50/70 dark:border-emerald-800 dark:from-emerald-950/50 dark:to-cyan-950/30">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
            🎉 {d.badge}
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
          <p className="mt-2 text-xs text-emerald-800/90 dark:text-emerald-100/90">{d.academyHint}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to="/me/following" className="btn-primary whitespace-nowrap text-xs">
            {d.openFollowing}
          </Link>
          <button
            type="button"
            className="btn whitespace-nowrap text-xs"
            onClick={() => setPending(false)}
          >
            {d.stayOnFeed}
          </button>
        </div>
      </div>
    </div>
  );
}

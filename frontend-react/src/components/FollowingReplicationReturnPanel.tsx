import { useEffect } from "react";
import { Link } from "react-router-dom";
import { burstConfetti } from "../lib/confetti";
import { REPLICATION_SHARE_FOLLOWING_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";

export default function FollowingReplicationReturnPanel() {
  const d = useLocale((s) => s.dict.followingReplicationReturn);
  const show =
    typeof window !== "undefined" && sessionStorage.getItem(REPLICATION_SHARE_FOLLOWING_KEY) === "1";

  useEffect(() => {
    if (!show) return;
    sessionStorage.removeItem(REPLICATION_SHARE_FOLLOWING_KEY);
    burstConfetti(2000);
  }, [show]);

  if (!show) return null;

  return (
    <div className="mb-4 card border border-emerald-200 bg-gradient-to-r from-emerald-50/90 to-teal-50/60 dark:border-emerald-900 dark:from-emerald-950/40 dark:to-teal-950/30">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-200">
        🔄 {d.badge}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-50">{d.title}</p>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{d.message}</p>
      <p className="mt-2 text-xs text-emerald-900/80 dark:text-emerald-100/80">{d.hint}</p>
      <Link to="#following-feed-grid" className="btn-primary mt-3 inline-block text-xs">
        {d.readPeers}
      </Link>
    </div>
  );
}

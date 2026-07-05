import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getFollowingFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { FOLLOWING_FEED_HIGHLIGHT_KEY, REPLICATION_SHARE_FOLLOWING_KEY } from "../lib/onboardingFocus";
import { useLocale } from "../store/locale";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";
import FollowingReplicationReturnPanel from "../components/FollowingReplicationReturnPanel";
import FollowingFeedRhythmCoachPanel from "../components/FollowingFeedRhythmCoachPanel";
import FollowingFeedWelcomePanel from "../components/FollowingFeedWelcomePanel";

export default function Following() {
  const { dict } = useLocale();
  const t = dict.following;
  const [highlightFirst, setHighlightFirst] = useState(
    () => typeof window !== "undefined" && sessionStorage.getItem(FOLLOWING_FEED_HIGHLIGHT_KEY) === "1",
  );
  const [replicationReturnActive] = useState(
    () => typeof window !== "undefined" && sessionStorage.getItem(REPLICATION_SHARE_FOLLOWING_KEY) === "1",
  );
  const firstCardRef = useRef<HTMLDivElement>(null);
  const q = useQuery({ queryKey: ["following-feed"], queryFn: getFollowingFeed });

  useEffect(() => {
    if (!highlightFirst || !q.data?.length) return;
    sessionStorage.removeItem(FOLLOWING_FEED_HIGHLIGHT_KEY);
    const timer = window.setTimeout(() => {
      firstCardRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 200);
    return () => window.clearTimeout(timer);
  }, [highlightFirst, q.data]);

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle} />
      <FollowingFeedWelcomePanel onHighlightReady={() => setHighlightFirst(true)} />
      <FollowingReplicationReturnPanel />
      <FollowingFeedRhythmCoachPanel
        hasReports={Boolean(q.data && q.data.length > 0)}
        highlightActive={highlightFirst}
        replicationReturnActive={replicationReturnActive}
      />
      {highlightFirst && q.data && q.data.length > 0 && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50/60 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">
          {t.highlightFirst}
        </div>
      )}
      {q.isLoading ? (
        <Spinner />
      ) : q.isError ? (
        <ErrorBox message={apiErrorMessage(q.error)} />
      ) : q.data && q.data.length > 0 ? (
        <div id="following-feed-grid" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {q.data.map((r, index) => (
            <div
              key={r.id}
              ref={index === 0 && highlightFirst ? firstCardRef : undefined}
              className={
                index === 0 && highlightFirst
                  ? "rounded-xl ring-2 ring-emerald-400 ring-offset-2 dark:ring-emerald-600"
                  : undefined
              }
            >
              <ReportCard report={r} markHandoffOnOpen={highlightFirst && index === 0} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title={t.emptyTitle}
          hint={t.emptyHint}
          action={
            <Link to="/feed" className="btn-primary mt-2">
              {t.goFeed}
            </Link>
          }
        />
      )}
    </div>
  );
}

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getFollowingFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";
import FollowingFeedWelcomePanel from "../components/FollowingFeedWelcomePanel";

export default function Following() {
  const { dict } = useLocale();
  const t = dict.following;
  const q = useQuery({ queryKey: ["following-feed"], queryFn: getFollowingFeed });

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle} />
      <FollowingFeedWelcomePanel />
      {q.isLoading ? (
        <Spinner />
      ) : q.isError ? (
        <ErrorBox message={apiErrorMessage(q.error)} />
      ) : q.data && q.data.length > 0 ? (
        <div id="following-feed-grid" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {q.data.map((r) => (
            <ReportCard key={r.id} report={r} />
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

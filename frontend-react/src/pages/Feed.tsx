import { useQuery } from "@tanstack/react-query";
import { getFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";
import { Link } from "react-router-dom";

export default function Feed() {
  const user = useAuth((s) => s.user);
  const f = useLocale((s) => s.dict.feed);
  const feed = useQuery({
    queryKey: ["feed"],
    queryFn: getFeed,
    enabled: Boolean(user),
  });

  if (!user) {
    return (
      <EmptyState
        title={f.loginTitle}
        hint={f.loginHint}
        action={
          <Link to="/login" className="btn-primary mt-2">
            {f.login}
          </Link>
        }
      />
    );
  }

  return (
    <div>
      <PageTitle title={f.title} subtitle={f.subtitle} />
      {feed.isLoading ? (
        <Spinner />
      ) : feed.isError ? (
        <ErrorBox message={apiErrorMessage(feed.error)} />
      ) : feed.data && feed.data.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {feed.data.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      ) : (
        <EmptyState title={f.emptyTitle} hint={f.emptyHint} />
      )}
    </div>
  );
}

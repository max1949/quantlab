import { useQuery } from "@tanstack/react-query";
import { getFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";
import { Link } from "react-router-dom";

export default function Feed() {
  const user = useAuth((s) => s.user);
  const feed = useQuery({
    queryKey: ["feed"],
    queryFn: getFeed,
    enabled: Boolean(user),
  });

  if (!user) {
    return (
      <EmptyState
        title="登录后查看研究广场"
        hint="看看大家都在研究什么"
        action={
          <Link to="/login" className="btn-primary mt-2">
            去登录
          </Link>
        }
      />
    );
  }

  return (
    <div>
      <PageTitle title="研究广场" subtitle="社区里最新的公开研究成果" />
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
        <EmptyState title="还没有公开研究" hint="成为第一个发布研究的人!" />
      )}
    </div>
  );
}

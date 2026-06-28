import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getFollowingFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";

export default function Following() {
  const q = useQuery({ queryKey: ["following-feed"], queryFn: getFollowingFeed });

  return (
    <div>
      <PageTitle title="关注动态" subtitle="你关注的研究员的最新研究" />
      {q.isLoading ? (
        <Spinner />
      ) : q.isError ? (
        <ErrorBox message={apiErrorMessage(q.error)} />
      ) : q.data && q.data.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {q.data.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="还没有关注动态"
          hint="去研究广场关注一些研究员吧"
          action={
            <Link to="/feed" className="btn-primary mt-2">
              去研究广场
            </Link>
          }
        />
      )}
    </div>
  );
}

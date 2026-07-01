import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getPublicFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";

export default function Feed() {
  const user = useAuth((s) => s.user);
  const f = useLocale((s) => s.dict.feed);
  useDocumentTitle(`${f.title} · QuantLab AI`);
  const feed = useQuery({
    queryKey: ["public-feed"],
    queryFn: getPublicFeed,
  });

  return (
    <div>
      <PageTitle title={f.title} subtitle={f.subtitle} />

      {!user && (
        <div className="mb-4 flex flex-col gap-3 rounded-xl border border-brand-200 bg-brand-50/60 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-brand-900 dark:bg-brand-950/40">
          <p className="text-sm text-slate-700 dark:text-slate-200">{f.guestBanner}</p>
          <div className="flex shrink-0 gap-2">
            <Link to="/login" className="btn-ghost">
              {f.guestLogin}
            </Link>
            <Link to="/register" className="btn-primary">
              {f.guestRegister}
            </Link>
          </div>
        </div>
      )}

      {feed.isLoading ? (
        <Spinner />
      ) : feed.isError ? (
        <ErrorBox message={apiErrorMessage(feed.error)} />
      ) : feed.data && feed.data.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {feed.data.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      ) : (
        <EmptyState
          title={f.emptyTitle}
          hint={f.emptyHint}
          action={
            user ? (
              <Link to="/templates" className="btn-primary mt-2">
                {f.emptyCta}
              </Link>
            ) : (
              <Link to="/register" className="btn-primary mt-2">
                {f.guestRegister}
              </Link>
            )
          }
        />
      )}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { getPublicFeed } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";
import ReportCard from "../components/ReportCard";
import FeedFollowCoachPanel from "../components/FeedFollowCoachPanel";
import NetworkReadyCoachPanel from "../components/NetworkReadyCoachPanel";

export default function Feed() {
  const user = useAuth((s) => s.user);
  const f = useLocale((s) => s.dict.feed);
  const rc = useLocale((s) => s.dict.reportCard);
  const [params] = useSearchParams();
  const highlightId = params.get("highlight");
  const focusFollow = params.get("focus") === "follow";
  const highlightRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const [sort, setSort] = useState<"top" | "latest">(
    highlightId ? "latest" : focusFollow ? "top" : "top",
  );
  const [graduatedOnly, setGraduatedOnly] = useState(focusFollow);
  useDocumentTitle(`${f.title} · QuantLab AI`);
  const feed = useQuery({
    queryKey: ["public-feed", sort, graduatedOnly, user?.id ?? "guest"],
    queryFn: () => getPublicFeed(sort, graduatedOnly),
  });

  useEffect(() => {
    if (!highlightId || !feed.data?.some((r) => r.id === highlightId)) return;
    const t = window.setTimeout(() => {
      highlightRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 120);
    return () => window.clearTimeout(t);
  }, [highlightId, feed.data]);

  useEffect(() => {
    if (!focusFollow || feed.isLoading) return;
    const t = window.setTimeout(() => {
      gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 180);
    return () => window.clearTimeout(t);
  }, [focusFollow, feed.isLoading, feed.data]);

  const discoverMasters = () => {
    setSort("top");
    setGraduatedOnly(true);
    window.setTimeout(() => {
      gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  };

  return (
    <div>
      <PageTitle title={f.title} subtitle={f.subtitle} />

      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          className={sort === "top" ? "btn-primary" : "btn-ghost"}
          onClick={() => setSort("top")}
        >
          {f.sortTop}
        </button>
        <button
          type="button"
          className={sort === "latest" ? "btn-primary" : "btn-ghost"}
          onClick={() => setSort("latest")}
        >
          {f.sortLatest}
        </button>
        <button
          type="button"
          className={graduatedOnly ? "btn-primary" : "btn-ghost"}
          onClick={() => setGraduatedOnly((v) => !v)}
        >
          {f.filterGraduated}
        </button>
      </div>

      <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-2 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300">
        <p className="mb-1.5 font-medium text-slate-700 dark:text-slate-200">{f.badgeLegendTitle}</p>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center gap-1">
            <span className="rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
              {rc.badgePaperGraduated}
            </span>
            {f.badgeLegendPaper}
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="rounded-full bg-brand-100 px-1.5 py-0.5 text-[10px] font-semibold text-brand-800 dark:bg-brand-950 dark:text-brand-200">
              {rc.badgePaperTracking}
            </span>
            {f.badgeLegendTracking}
          </span>
        </div>
      </div>

      {user && <FeedFollowCoachPanel onDiscoverMasters={discoverMasters} />}
      {user && <NetworkReadyCoachPanel />}

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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" ref={gridRef}>
          {highlightId && feed.data.some((r) => r.id === highlightId) && (
            <div className="col-span-full rounded-lg border border-emerald-200 bg-emerald-50/60 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">
              {f.highlightBanner}
            </div>
          )}
          {feed.data.map((r) => (
            <div
              key={r.id}
              ref={r.id === highlightId ? highlightRef : undefined}
              className={
                r.id === highlightId
                  ? "rounded-xl ring-2 ring-emerald-400 ring-offset-2 dark:ring-emerald-600"
                  : undefined
              }
            >
              <ReportCard report={r} showFollow />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title={graduatedOnly ? f.emptyGraduatedTitle : f.emptyTitle}
          hint={graduatedOnly ? f.emptyGraduatedHint : f.emptyHint}
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

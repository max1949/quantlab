import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getShareCard, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useLocale } from "../store/locale";
import { GradeBadge, Spinner } from "../components/ui";

export default function SharePage() {
  const { dict } = useLocale();
  const t = dict.share;
  const { token = "" } = useParams();
  const q = useQuery({
    queryKey: ["share", token],
    queryFn: () => getShareCard(token),
  });

  useEffect(() => {
    void trackEvent("share_view", { token });
  }, [token]);

  useDocumentTitle(q.data?.card?.title ? `${q.data.card.title} · ${dict.brand}` : undefined);

  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4 py-10">
      <div className="w-full max-w-lg">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            Q
          </span>
          <span className="text-lg font-semibold">{dict.brand}</span>
        </Link>

        {q.isLoading ? (
          <Spinner />
        ) : q.isError ? (
          <div className="card text-center text-slate-500">
            {apiErrorMessage(q.error, t.invalid)}
          </div>
        ) : (
          <ShareCardView card={q.data!.card} views={q.data!.views} />
        )}

        <div className="mt-6 rounded-2xl bg-white p-5 text-center shadow-sm">
          <p className="font-medium text-slate-700">{t.pitch}</p>
          <p className="mt-1 text-sm text-slate-400">{t.pitchDesc}</p>
          <Link to="/register" className="btn-primary mt-3 inline-flex px-6">
            {t.cta}
          </Link>
        </div>
      </div>
    </div>
  );
}

function ShareCardView({
  card,
  views,
}: {
  card: import("../api/types").ShareCard;
  views: number;
}) {
  const { dict } = useLocale();
  const t = dict.share;
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md">
      <div className="bg-gradient-to-r from-brand-600 to-brand-500 px-6 py-5 text-white">
        <p className="text-xs uppercase tracking-wide text-brand-100">{t.badge}</p>
        <h1 className="mt-1 text-xl font-bold">{card.title ?? t.defaultTitle}</h1>
        <p className="mt-2 text-sm text-brand-50">
          {t.by} {card.researcher ?? "—"}
          {card.symbol ? ` · ${card.symbol}` : ""}
        </p>
      </div>
      <div className="space-y-4 px-6 py-5">
        <div className="flex items-center gap-2">
          <GradeBadge grade={card.grade} />
          <span className="text-xs text-slate-400">{t.views(views)}</span>
        </div>
        {card.summary && (
          <div>
            <p className="text-xs font-medium text-slate-400">{t.summary}</p>
            <p className="mt-1 text-sm leading-relaxed text-slate-700">{card.summary}</p>
          </div>
        )}
        {card.hypothesis && (
          <div>
            <p className="text-xs font-medium text-slate-400">{t.hypothesis}</p>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">{card.hypothesis}</p>
          </div>
        )}
      </div>
    </div>
  );
}

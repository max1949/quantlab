import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { shareReport, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { celebrateFirstShare } from "../lib/firstShare";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

type Props = {
  reportId: string;
};

export default function ReportShareCoach({ reportId }: Props) {
  const t = useLocale((s) => s.dict.report);
  const d = useLocale((s) => s.dict.dashboard);
  const notify = useUi((s) => s.notify);
  const refreshMe = useAuth((s) => s.refreshMe);
  const qc = useQueryClient();
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const share = useMutation({
    mutationFn: () => shareReport(reportId),
    onSuccess: async (res) => {
      void trackEvent("share_created", { report: reportId });
      const url = `${window.location.origin}/share/${res.token}`;
      setShareUrl(url);
      const first = celebrateFirstShare(
        res,
        { celebrate: t.firstShareCelebrate, academyXpEarned: d.academyXpEarned },
        notify,
      );
      if (!first) notify(t.shareCreated, "success");
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      void qc.invalidateQueries({ queryKey: ["public-feed"] });
      void trackEvent("share_success_feed_prompt", { report_id: reportId });
      await refreshMe();
      requestAnimationFrame(() => {
        rootRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    },
    onError: (e) => notify(apiErrorMessage(e, t.shareFail), "error"),
  });

  useEffect(() => {
    if (window.location.hash === "#report-share") {
      requestAnimationFrame(() => {
        rootRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }, []);

  async function copyLink() {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    notify(t.copied, "success");
  }

  const feedHref = `/feed?highlight=${reportId}`;

  if (shareUrl) {
    return (
      <div
        id="report-share"
        ref={rootRef}
        className="mt-6 card border border-emerald-200 bg-gradient-to-br from-emerald-50/90 to-brand-50/40 dark:border-emerald-900 dark:from-emerald-950/40 dark:to-brand-950/20"
      >
        <p className="font-semibold text-emerald-800 dark:text-emerald-200">{t.shareSuccessTitle}</p>
        <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-300">{t.shareSuccessDesc}</p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to={feedHref}
            className="btn-primary"
            onClick={() => void trackEvent("share_goto_feed", { report_id: reportId })}
          >
            {t.shareViewOnFeed}
          </Link>
          <button type="button" className="btn" onClick={copyLink}>
            {t.copyLink}
          </button>
          <a className="btn-ghost" href={shareUrl} target="_blank" rel="noreferrer">
            {t.preview}
          </a>
        </div>

        <div className="mt-4">
          <label className="label text-xs text-slate-500">{t.shareLinkLabel}</label>
          <input className="input mt-1 text-sm" value={shareUrl} readOnly />
        </div>
      </div>
    );
  }

  return (
    <div id="report-share" ref={rootRef} className="mt-6 card bg-brand-50/40 dark:bg-brand-950/20">
      <h3 className="font-semibold text-slate-800 dark:text-slate-100">📣 {t.shareTitle}</h3>
      <p className="mt-1 text-sm text-slate-500">{t.shareDesc}</p>
      <button
        className="btn-primary mt-3"
        disabled={share.isPending}
        onClick={() => share.mutate()}
      >
        {share.isPending ? t.shareGenerating : t.shareGenerate}
      </button>
    </div>
  );
}

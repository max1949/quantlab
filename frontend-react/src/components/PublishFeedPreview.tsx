import { Link } from "react-router-dom";
import { useLocale } from "../store/locale";
import type { ProjectQuality } from "../api/endpoints";

type Props = {
  quality: ProjectQuality;
  published: boolean;
};

export default function PublishFeedPreview({ quality, published }: Props) {
  const p = useLocale((s) => s.dict.projectDetail);
  const rc = useLocale((s) => s.dict.reportCard);
  const preview = quality.feed_preview;
  if (published || !preview) return null;

  return (
    <div className="mb-4 rounded-xl border border-brand-200 bg-brand-50/50 px-4 py-3 dark:border-brand-900 dark:bg-brand-950/30">
      <p className="font-medium text-slate-800 dark:text-slate-100">{p.feedPreviewTitle}</p>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
        {preview.publish_ready ? p.feedPreviewReady : p.feedPreviewLocked}
      </p>
      {preview.publish_ready && (
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {p.feedPreviewBaseBadge}
          </span>
          {preview.paper_graduated && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
              {rc.badgePaperGraduated}
            </span>
          )}
          {preview.paper_tracking && (
            <span className="rounded-full bg-brand-100 px-2 py-0.5 text-[10px] font-semibold text-brand-800 dark:bg-brand-950 dark:text-brand-200">
              {rc.badgePaperTracking}
            </span>
          )}
        </div>
      )}
      {preview.publish_ready && !preview.paper_graduated && (
        <p className="mt-2 text-xs text-amber-700 dark:text-amber-200">{p.feedPreviewPaperHint}</p>
      )}
      {preview.publish_ready && (
        <Link to="/feed" className="mt-2 inline-block text-xs font-medium text-brand-600 hover:underline">
          {p.feedPreviewBrowse} →
        </Link>
      )}
    </div>
  );
}

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import type { ProjectQuality } from "../api/endpoints";
import { localizedAcademyTitle } from "../lib/academy";
import { NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";

type Props = {
  quality: ProjectQuality;
  onAction: (action: string) => void;
  isPublished?: boolean;
  hasReport?: boolean;
  reportId?: string | null;
  publishReady?: boolean;
};

const STAGE_KEYS = ["start", "backtest", "validate", "graduate", "paper", "track", "share"] as const;

export default function MasteryPathPanel({
  quality,
  onAction,
  isPublished = false,
  hasReport = false,
  reportId = null,
  publishReady = false,
}: Props) {
  const m = useLocale((s) => s.dict.masteryPath);
  const atl = useLocale((s) => s.dict.academyTaskLabels);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });
  const following = journey.data?.social_following_count ?? 0;
  const networkReady = following >= NETWORK_FOLLOW_TARGET;
  const mastery = quality.mastery;
  if (!mastery) return null;

  const currentIdx = mastery.stage_index ?? 0;
  const academyTasks =
    mastery.stage === "share" ? quality.academy_stage_tasks : quality.academy_next_tasks;
  const pendingAcademyTasks = (academyTasks ?? []).filter((t) => !t.completed);

  return (
    <div className="mb-6 card border border-brand-100 bg-brand-50/30 dark:border-brand-900 dark:bg-brand-950/20">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{m.title}</h3>
          <p className="text-xs text-slate-500">{m.subtitle}</p>
        </div>
        <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900 dark:text-brand-200">
          {m.progress(mastery.progress_pct ?? 0)}
        </span>
      </div>

      <ol className="mb-4 grid gap-2 sm:grid-cols-7">
        {STAGE_KEYS.map((key, idx) => {
          const done = idx < currentIdx || (key === "share" && quality.mastery?.stage === "share");
          const active = idx === currentIdx;
          return (
            <li
              key={key}
              className={`rounded-lg border px-2 py-2 text-center text-xs ${
                done
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
                  : active
                    ? "border-brand-400 bg-white font-semibold text-brand-800 ring-2 ring-brand-300 dark:bg-slate-900 dark:text-brand-200"
                    : "border-slate-200 bg-white/50 text-slate-400 dark:border-slate-700 dark:bg-slate-900/30"
              }`}
            >
              {done && "✓ "}
              {m.stages[key]}
            </li>
          );
        })}
      </ol>

      {pendingAcademyTasks.length > 0 && (
        <div className="mb-3 rounded-lg border border-amber-100 bg-amber-50/60 px-3 py-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
          {pendingAcademyTasks
            .slice(0, mastery.stage === "share" ? 4 : 2)
            .map((t) => (
              <div key={t.code} className="mt-0.5 first:mt-0">
                <p>
                  🏅 {m.academyStagePending(localizedAcademyTitle(t.code, t.title, atl), t.xp_reward)}
                </p>
                {mastery.stage === "share" && t.code === "network-radar" && !networkReady && (
                  <Link to="/feed?focus=follow" className="ml-4 inline-block text-[11px] font-medium text-brand-700">
                    {m.shareNetworkCta}
                  </Link>
                )}
                {mastery.stage === "share" && t.code === "master-replication" && networkReady && (
                  <Link to="/me/following" className="ml-4 inline-block text-[11px] font-medium text-brand-700">
                    {m.shareReplicationCta}
                  </Link>
                )}
              </div>
            ))}
        </div>
      )}

      {mastery.stage === "share" ? (
        <div className="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm text-brand-900 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-100">
          <p className="font-medium">{m.shareReady}</p>
          <p className="mt-1 text-xs opacity-90">{m.shareHint}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {!hasReport && (
              <button type="button" className="btn-primary text-xs" onClick={() => onAction("report")}>
                {m.shareReportCta}
              </button>
            )}
            {hasReport && !isPublished && publishReady && (
              <button type="button" className="btn-primary text-xs" onClick={() => onAction("publish")}>
                {m.sharePublishCta}
              </button>
            )}
            {hasReport && reportId && (
              <Link to={`/reports/${reportId}#report-share`} className="btn text-xs">
                {m.shareCardCta}
              </Link>
            )}
            {networkReady && (
              <Link to="/me/following" className="btn text-xs">
                {m.shareFollowingCta}
              </Link>
            )}
          </div>
        </div>
      ) : quality.paper_ready && mastery.stage === "track" && mastery.decay_attention ? (
        <div
          className={`rounded-lg border px-3 py-2 text-sm ${
            mastery.decay_status === "alert"
              ? "border-rose-200 bg-rose-50 text-rose-900 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-100"
              : "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100"
          }`}
        >
          <p className="font-medium">
            {mastery.decay_status === "alert" ? m.decayAlert : m.decayWatch}
          </p>
          {quality.paper_decay?.reasons && quality.paper_decay.reasons.length > 0 && (
            <ul className="mt-1 list-inside list-disc text-xs opacity-90">
              {quality.paper_decay.reasons.slice(0, 2).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          <button type="button" className="btn mt-2 text-xs" onClick={() => onAction("revalidate")}>
            {m.decayCta}
          </button>
        </div>
      ) : quality.paper_ready && mastery.stage === "track" ? (
        <div className="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm text-brand-900 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-100">
          <p className="font-medium">{m.trackReady}</p>
          <button type="button" className="btn mt-2 text-xs" onClick={() => onAction("track")}>
            {m.trackCta}
          </button>
        </div>
      ) : quality.paper_ready ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
          <p className="font-medium">{m.paperReady}</p>
          <button type="button" className="btn-primary mt-2 text-xs" onClick={() => onAction("paper")}>
            {m.paperCta}
          </button>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white/70 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900/40">
          <p className="font-medium text-slate-700 dark:text-slate-200">{m.nextLabel(m.stages[mastery.next_action as keyof typeof m.stages] ?? mastery.next_action)}</p>
          {quality.paper_reasons && quality.paper_reasons.length > 0 && (
            <ul className="mt-1 list-inside list-disc text-xs text-slate-500">
              {quality.paper_reasons.slice(0, 3).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="btn mt-2 text-xs"
            onClick={() => onAction(mastery.next_action)}
          >
            {m.goNext}
          </button>
        </div>
      )}
    </div>
  );
}

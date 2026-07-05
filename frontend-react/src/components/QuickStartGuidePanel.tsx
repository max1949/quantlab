import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { enrollChallenge, getResearchJourney } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { celebrateChallengeEnroll } from "../lib/challengeEnroll";
import { useLocale } from "../store/locale";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import HandbookExportButtons from "./HandbookExportButtons";
import { stageToCtaLabel } from "../lib/nav";
import { Spinner } from "./ui";

const DISMISS_KEY = "quantlab-quickstart-dismissed";

function readDismissedProgress(): number {
  const raw = localStorage.getItem(DISMISS_KEY);
  if (!raw || raw === "1") return raw === "1" ? 999 : -1;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) ? n : -1;
}

export default function QuickStartGuidePanel() {
  const d = useLocale((s) => s.dict.quickstartGuide);
  const sprintLabels = useLocale((s) => s.dict.beginnerSprint);
  const handbook = useLocale((s) => s.dict.beginnerHandbook);
  const challengePage = useLocale((s) => s.dict.challengesPage);
  const dash = useLocale((s) => s.dict.dashboard);
  const stages = useLocale((s) => s.dict.stages);
  const notify = useUi((s) => s.notify);
  const refreshMe = useAuth((s) => s.refreshMe);
  const qc = useQueryClient();
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const guide = journey.data?.quickstart_guide;
  const sprint = journey.data?.beginner_sprint;
  const [hideAfterDismiss, setHideAfterDismiss] = useState(false);
  const dismissedProgress = readDismissedProgress();
  const dismissed =
    hideAfterDismiss ||
    dismissedProgress >= 999 ||
    (guide != null && dismissedProgress >= guide.progress);

  const enroll = useMutation({
    mutationFn: () => enrollChallenge(sprint!.challenge_code),
    onSuccess: async (data) => {
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      void qc.invalidateQueries({ queryKey: ["challenge-progress", sprint?.challenge_code] });
      void qc.invalidateQueries({ queryKey: ["researcher"] });
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      celebrateChallengeEnroll(
        data,
        { ...sprintLabels, academyXpEarned: dash.academyXpEarned },
        notify,
      );
      await refreshMe();
    },
    onError: (e) => notify(apiErrorMessage(e, challengePage.enrollFail), "error"),
  });

  if (dismissed) return null;
  if (journey.isLoading) return <Spinner />;
  if (!guide) return null;

  const current = guide.steps[guide.current_index];
  const ctaLabel =
    current && current.cta_action in stages
      ? stageToCtaLabel(current.cta_action, stages)
      : d.ctaDefault;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, String(guide.progress));
    setHideAfterDismiss(true);
  };

  return (
    <div className="card border border-sky-200 bg-gradient-to-r from-sky-50/90 to-indigo-50/50 dark:border-sky-900 dark:from-sky-950/40 dark:to-indigo-950/20">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-300">
              {guide.title}
            </p>
            <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-800 dark:bg-sky-900/60 dark:text-sky-200">
              {d.progress(guide.progress, guide.total)}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{guide.subtitle}</p>

          <ol className="mt-4 space-y-3">
            {guide.steps.map((step, i) => {
              const isCurrent = i === guide.current_index && !step.done;
              return (
                <li
                  key={step.key}
                  className={`flex gap-3 rounded-lg border px-3 py-2 ${
                    step.done
                      ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/30"
                      : isCurrent
                        ? "border-sky-300 bg-white/80 shadow-sm dark:border-sky-700 dark:bg-slate-900/50"
                        : "border-slate-200 bg-white/40 dark:border-slate-700 dark:bg-slate-900/20"
                  }`}
                >
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      step.done
                        ? "bg-emerald-500 text-white"
                        : isCurrent
                          ? "bg-sky-500 text-white"
                          : "bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {step.done ? "✓" : i + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p
                        className={`text-sm font-medium ${
                          step.done
                            ? "text-emerald-800 dark:text-emerald-200"
                            : "text-slate-800 dark:text-slate-100"
                        }`}
                      >
                        {step.label}
                      </p>
                      {isCurrent && (
                        <span className="rounded bg-sky-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-sky-700 dark:bg-sky-900/60 dark:text-sky-200">
                          {guide.current_badge}
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{step.hint}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>

        {current && !current.done && (
          <div className="flex shrink-0 flex-wrap gap-2 sm:flex-col sm:items-stretch">
            <Link to={current.cta_path} className="btn-primary whitespace-nowrap text-xs">
              {ctaLabel}
            </Link>
            <button type="button" className="btn whitespace-nowrap text-xs" onClick={dismiss}>
              {d.dismiss}
            </button>
          </div>
        )}
        {guide.progress === guide.total && (
          <button type="button" className="btn shrink-0 text-xs" onClick={dismiss}>
            {d.dismiss}
          </button>
        )}
      </div>

      {sprint && (
        <div className="mt-4 border-t border-sky-200 pt-3 dark:border-sky-800">
          <p className="text-xs font-semibold text-sky-800 dark:text-sky-200">{sprint.title}</p>
          <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{sprint.message}</p>
          {sprint.cta_action === "enroll_challenge" && !sprint.challenge_enrolled ? (
            <button
              type="button"
              className="btn-primary mt-2 text-xs"
              disabled={enroll.isPending}
              onClick={() => enroll.mutate()}
            >
              {enroll.isPending ? sprintLabels.enrolling : sprintLabels.enrollCta}
            </button>
          ) : (
            <Link
              to={sprint.cta_path}
              className="mt-2 inline-block text-xs font-medium text-brand-600 hover:underline"
            >
              {sprintLabels.viewCta}
            </Link>
          )}
        </div>
      )}
      <div className="mt-4 border-t border-sky-200 pt-3 dark:border-sky-800">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-300">
          {handbook.title}
        </p>
        <HandbookExportButtons compact />
      </div>
    </div>
  );
}

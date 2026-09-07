import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  challengeProgress,
  enrollChallenge,
  getCertificate,
  listChallenges,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { celebrateChallengeEnroll } from "../lib/challengeEnroll";
import { useLocale } from "../store/locale";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import ChallengeNetworkCoachPanel from "../components/ChallengeNetworkCoachPanel";

/**
 * Milestone CTAs — product semantics:
 * - paper_graduated: quality gate (assess_factor_paper), NOT legacy paper_orders
 * - first_paper_order: canonical PaperRun fills
 */
const MILESTONE_CTA: Record<string, { to: string; label: string }> = {
  first_factor: { to: "/templates", label: "去创建因子" },
  first_oos: { to: "/projects", label: "去做验证" },
  stack_factor: { to: "/projects", label: "去组合因子" },
  network_radar: { to: "/feed?focus=follow", label: "去关注研究员" },
  first_paper_order: { to: "/paper", label: "去正式模拟交易" },
  paper_graduated: { to: "/projects", label: "查看项目质量 / 毕业线差距" },
  research_share: { to: "/projects", label: "去生成分享卡" },
  first_report: { to: "/projects", label: "去写研究报告" },
};

export default function Challenges() {
  const { dict } = useLocale();
  const t = dict.challengesPage;
  const sprintLabels = dict.beginnerSprint;
  const dash = dict.dashboard;
  const atl = dict.academyTaskLabels;
  const notify = useUi((s) => s.notify);
  const refreshMe = useAuth((s) => s.refreshMe);
  const qc = useQueryClient();
  const [code, setCode] = useState<string | null>(null);

  const challenges = useQuery({
    queryKey: ["challenges"],
    queryFn: listChallenges,
  });

  useEffect(() => {
    if (!code && challenges.data && challenges.data.length > 0) {
      setCode(challenges.data[0].code);
    }
  }, [challenges.data, code]);

  const progress = useQuery({
    queryKey: ["challenge-progress", code],
    queryFn: () => challengeProgress(code!),
    enabled: Boolean(code),
    retry: false,
  });

  const enroll = useMutation({
    mutationFn: () => enrollChallenge(code!),
    onSuccess: async (data) => {
      qc.setQueryData(["challenge-progress", code], data);
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
      celebrateChallengeEnroll(
        data,
        {
          enrollSuccess: t.enrollSuccess,
          enrollSynced: sprintLabels.enrollSynced,
          enrollReward: sprintLabels.enrollReward,
          academyXpEarned: dash.academyXpEarned,
          academyTaskLabels: atl,
        },
        notify,
      );
      await refreshMe();
    },
    onError: (e) => notify(apiErrorMessage(e, t.enrollFail), "error"),
  });

  const cert = useMutation({
    mutationFn: () => getCertificate(code!),
    onSuccess: (c) => notify(t.certIssued(c.certificate_code), "success"),
    onError: (e) => notify(apiErrorMessage(e, t.certNotReady), "error"),
  });

  const list = challenges.data ?? [];
  const multi = list.length > 1;

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle} />
      <ChallengeNetworkCoachPanel />

      {challenges.isLoading ? (
        <Spinner />
      ) : challenges.isError ? (
        <ErrorBox message={apiErrorMessage(challenges.error)} />
      ) : list.length > 0 ? (
        <>
          {/*
            Product semantic: challenge codes are a *selector tab* when multiple exist.
            With a single challenge (or already selected), do NOT render a primary CTA-looking button
            that no-ops when clicked — that was the dead-click UX.
          */}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            {multi ? (
              list.map((c) => {
                const selected = code === c.code;
                return (
                  <button
                    key={c.code}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => {
                      if (!selected) setCode(c.code);
                    }}
                    className={`rounded-lg px-4 py-2 text-sm font-medium ${
                      selected
                        ? "cursor-default bg-brand-600 text-white"
                        : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-700"
                    }`}
                  >
                    {c.title}
                    {selected ? " · 当前" : ""}
                  </button>
                );
              })
            ) : (
              <div
                className="inline-flex items-center rounded-lg bg-brand-50 px-4 py-2 text-sm font-medium text-brand-800 ring-1 ring-brand-200 dark:bg-brand-950 dark:text-brand-100 dark:ring-brand-800"
                role="status"
                aria-label="当前挑战"
              >
                {list[0].title}
                <span className="ml-2 text-xs font-normal text-brand-600 dark:text-brand-300">当前挑战</span>
              </div>
            )}
          </div>

          {progress.isLoading ? (
            <Spinner />
          ) : progress.data ? (
            <ProgressView
              data={progress.data}
              onClaim={() => cert.mutate()}
              claiming={cert.isPending}
            />
          ) : (
            <div className="card text-center">
              <p className="text-slate-600 dark:text-slate-300">{t.enrollHint}</p>
              <button
                type="button"
                className="btn-primary mt-3"
                disabled={enroll.isPending}
                onClick={() => enroll.mutate()}
              >
                {enroll.isPending ? t.enrolling : t.enroll}
              </button>
            </div>
          )}
        </>
      ) : (
        <ErrorBox message={t.empty} />
      )}
    </div>
  );
}

function ProgressView({
  data,
  onClaim,
  claiming,
}: {
  data: import("../api/types").ChallengeProgress;
  onClaim: () => void;
  claiming: boolean;
}) {
  const { dict } = useLocale();
  const t = dict.challengesPage;
  const allDone = data.completed_count >= data.total;
  const pending = data.milestones.filter((m) => !m.completed);
  return (
    <div>
      <div className="card">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <p className="font-semibold text-slate-800 dark:text-slate-100">{data.title}</p>
            <p className="text-sm text-slate-400">
              {t.completed(data.completed_count, data.total, data.reward_points)}
            </p>
            {pending.length === 1 ? (
              <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">
                还差 1 项：{pending[0].title}
              </p>
            ) : null}
          </div>
          {data.certificate_code ? (
            <span className="badge bg-emerald-100 text-emerald-700">
              {t.certLabel(data.certificate_code)}
            </span>
          ) : (
            <button
              type="button"
              className={
                allDone
                  ? "btn-primary shrink-0"
                  : "shrink-0 cursor-not-allowed rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-400 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-500 dark:ring-slate-700"
              }
              disabled={!allDone || claiming}
              title={!allDone ? "完成全部里程碑后可领取" : undefined}
              aria-disabled={!allDone || claiming}
              onClick={onClaim}
            >
              {allDone ? t.claimCert : t.claimCertLocked}
            </button>
          )}
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${data.percent}%` }}
          />
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {data.milestones.map((m) => {
          const cta = !m.completed ? MILESTONE_CTA[m.code] : null;
          const secondary =
            !m.completed && m.code === "paper_graduated"
              ? { to: "/evidence", label: "打开证据系统了解判定" }
              : !m.completed && m.code === "first_paper_order"
                ? { to: "/evidence", label: "先看证据再模拟" }
                : null;
          return (
            <div
              key={m.code}
              className={`card flex items-start justify-between gap-2 ${
                m.completed
                  ? "border-emerald-200 bg-emerald-50/40 dark:border-emerald-900 dark:bg-emerald-950/30"
                  : ""
              }`}
            >
              <div className="min-w-0">
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  {m.completed ? "✅ " : "⬜ "}
                  {m.title}
                </p>
                {m.journey_label && (
                  <p className="text-xs text-brand-600 dark:text-brand-400">
                    {t.journeyStep(m.journey_label)}
                  </p>
                )}
                {m.mastery_stage_label && (
                  <p className="text-xs text-emerald-700 dark:text-emerald-300">
                    {t.masteryStep(m.mastery_stage_label)}
                  </p>
                )}
                <p className="text-xs text-slate-400">{t.day(m.day)}</p>
                {(m.pending_hint_zh || m.pending_hint_en) && !m.completed ? (
                  <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                    {m.pending_hint_zh || m.pending_hint_en}
                  </p>
                ) : null}
                {cta ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Link
                      to={cta.to}
                      className="inline-block rounded-md bg-brand-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-brand-700"
                    >
                      {cta.label} →
                    </Link>
                    {secondary ? (
                      <Link
                        to={secondary.to}
                        className="inline-block text-xs font-medium text-brand-600 underline dark:text-brand-300"
                      >
                        {secondary.label} →
                      </Link>
                    ) : null}
                  </div>
                ) : null}
              </div>
              <span className="badge shrink-0">+{m.reward_points}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

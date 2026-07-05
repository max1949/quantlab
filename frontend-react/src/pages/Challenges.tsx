import { useEffect, useState } from "react";
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

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle} />
      <ChallengeNetworkCoachPanel />

      {challenges.isLoading ? (
        <Spinner />
      ) : challenges.isError ? (
        <ErrorBox message={apiErrorMessage(challenges.error)} />
      ) : challenges.data && challenges.data.length > 0 ? (
        <>
          <div className="mb-4 flex flex-wrap gap-2">
            {challenges.data.map((c) => (
              <button
                key={c.code}
                onClick={() => setCode(c.code)}
                className={`rounded-lg px-4 py-2 text-sm font-medium ${
                  code === c.code
                    ? "bg-brand-600 text-white"
                    : "bg-white text-slate-600 ring-1 ring-slate-200"
                }`}
              >
                {c.title}
              </button>
            ))}
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
              <p className="text-slate-600">{t.enrollHint}</p>
              <button
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
  return (
    <div>
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold text-slate-800">{data.title}</p>
            <p className="text-sm text-slate-400">
              {t.completed(data.completed_count, data.total, data.reward_points)}
            </p>
          </div>
          {data.certificate_code ? (
            <span className="badge bg-emerald-100 text-emerald-700">
              {t.certLabel(data.certificate_code)}
            </span>
          ) : (
            <button
              className="btn-primary"
              disabled={!allDone || claiming}
              onClick={onClaim}
            >
              {allDone ? t.claimCert : t.claimCertLocked}
            </button>
          )}
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${data.percent}%` }}
          />
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {data.milestones.map((m) => (
          <div
            key={m.code}
            className={`card flex items-center justify-between ${
              m.completed ? "border-emerald-200 bg-emerald-50/40" : ""
            }`}
          >
            <div>
              <p className="font-medium text-slate-700">
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
            </div>
            <span className="badge">+{m.reward_points}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

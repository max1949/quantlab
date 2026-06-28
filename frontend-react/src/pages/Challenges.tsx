import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  challengeProgress,
  enrollChallenge,
  getCertificate,
  listChallenges,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Challenges() {
  const notify = useUi((s) => s.notify);
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
    onSuccess: (data) => {
      qc.setQueryData(["challenge-progress", code], data);
      notify("报名成功! 完成里程碑即可领取证书", "success");
    },
    onError: (e) => notify(apiErrorMessage(e, "报名失败"), "error"),
  });

  const cert = useMutation({
    mutationFn: () => getCertificate(code!),
    onSuccess: (c) =>
      notify(`证书已颁发: ${c.certificate_code}`, "success"),
    onError: (e) => notify(apiErrorMessage(e, "尚未全部完成"), "error"),
  });

  return (
    <div>
      <PageTitle
        title="30 天研究挑战"
        subtitle="按里程碑完成研究动作, 拿奖励积分和完成证书。"
      />

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
              <p className="text-slate-600">报名后开始你的 30 天研究挑战</p>
              <button
                className="btn-primary mt-3"
                disabled={enroll.isPending}
                onClick={() => enroll.mutate()}
              >
                {enroll.isPending ? "报名中…" : "立即报名"}
              </button>
            </div>
          )}
        </>
      ) : (
        <ErrorBox message="暂无可参加的挑战 (运行 scripts/seed-challenge.ps1 初始化)" />
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
  const allDone = data.completed_count >= data.total;
  return (
    <div>
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold text-slate-800">{data.title}</p>
            <p className="text-sm text-slate-400">
              已完成 {data.completed_count}/{data.total} · 奖励积分{" "}
              {data.reward_points}
            </p>
          </div>
          {data.certificate_code ? (
            <span className="badge bg-emerald-100 text-emerald-700">
              证书 {data.certificate_code}
            </span>
          ) : (
            <button
              className="btn-primary"
              disabled={!allDone || claiming}
              onClick={onClaim}
            >
              {allDone ? "领取证书" : "完成全部解锁证书"}
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
              <p className="text-xs text-slate-400">第 {m.day} 天</p>
            </div>
            <span className="badge">+{m.reward_points}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

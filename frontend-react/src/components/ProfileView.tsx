import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ResearcherProfile } from "../api/types";
import { follow, unfollow } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { Stat } from "./ui";

export default function ProfileView({
  profile,
  canFollow,
  queryKey,
}: {
  profile: ResearcherProfile;
  canFollow: boolean;
  queryKey: unknown[];
}) {
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);

  const toggle = useMutation({
    mutationFn: () =>
      profile.is_following ? unfollow(profile.user_id) : follow(profile.user_id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey });
      notify(profile.is_following ? "已取消关注" : "已关注", "success");
    },
    onError: (e) => notify(apiErrorMessage(e, "操作失败"), "error"),
  });

  return (
    <div>
      <div className="card">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="grid h-14 w-14 place-items-center rounded-full bg-brand-100 text-lg font-bold text-brand-700">
              {profile.username.slice(0, 2).toUpperCase()}
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                {profile.username}
              </h1>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                <span className="badge">{profile.level_label}</span>
                <span>关注 {profile.following}</span>
                <span>粉丝 {profile.followers}</span>
              </div>
            </div>
          </div>
          {canFollow && (
            <button
              className={profile.is_following ? "btn-ghost" : "btn-primary"}
              disabled={toggle.isPending}
              onClick={() => toggle.mutate()}
            >
              {profile.is_following ? "已关注" : "+ 关注"}
            </button>
          )}
        </div>

        {profile.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1">
            {profile.tags.map((t) => (
              <span key={t} className="badge">
                #{t}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="研究信用分"
          value={profile.research_contribution_score.toFixed(1)}
        />
        <Stat label="竞技评分" value={profile.research_score.toFixed(1)} />
        <Stat label="奖励积分" value={profile.reward_points} />
        <Stat label="经验" value={profile.experience} />
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="研究项目" value={profile.project_count} />
        <Stat label="因子" value={profile.factor_count} />
        <Stat
          label="有效验证"
          value={`${profile.effective_validation_count}/${profile.validation_count}`}
        />
        <Stat label="研究报告" value={profile.report_count} />
      </div>
    </div>
  );
}

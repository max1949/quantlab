import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ResearcherProfile } from "../api/types";
import { follow, unfollow } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
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
  const { dict } = useLocale();
  const t = dict.profile;
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);

  const toggle = useMutation({
    mutationFn: () =>
      profile.is_following ? unfollow(profile.user_id) : follow(profile.user_id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey });
      notify(profile.is_following ? t.unfollowed : t.followed, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, t.followFail), "error"),
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
              <h1 className="text-xl font-bold text-slate-900">{profile.username}</h1>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                <span className="badge">{profile.level_label}</span>
                <span>
                  {t.following} {profile.following}
                </span>
                <span>
                  {t.followers} {profile.followers}
                </span>
              </div>
            </div>
          </div>
          {canFollow && (
            <button
              className={profile.is_following ? "btn-ghost" : "btn-primary"}
              disabled={toggle.isPending}
              onClick={() => toggle.mutate()}
            >
              {profile.is_following ? t.followingBtn : t.follow}
            </button>
          )}
        </div>

        {profile.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1">
            {profile.tags.map((tag) => (
              <span key={tag} className="badge">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label={t.researchCredit}
          value={profile.research_contribution_score.toFixed(1)}
        />
        <Stat label={t.arenaScore} value={profile.research_score.toFixed(1)} />
        <Stat label={t.rewardPoints} value={profile.reward_points} />
        <Stat label={t.experience} value={profile.experience} />
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label={t.projects} value={profile.project_count} />
        <Stat label={t.factors} value={profile.factor_count} />
        <Stat
          label={t.validations}
          value={`${profile.effective_validation_count}/${profile.validation_count}`}
        />
        <Stat label={t.reports} value={profile.report_count} />
      </div>
    </div>
  );
}

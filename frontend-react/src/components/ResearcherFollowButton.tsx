import { useMutation, useQueryClient } from "@tanstack/react-query";
import { follow, trackEvent, unfollow } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { burstConfetti } from "../lib/confetti";
import { FIRST_FEED_FOLLOW_WELCOME_KEY } from "../lib/onboardingFocus";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

type Props = {
  ownerId: string;
  isFollowing?: boolean | null;
  reportId?: string;
  compact?: boolean;
};

export default function ResearcherFollowButton({
  ownerId,
  isFollowing,
  reportId,
  compact = false,
}: Props) {
  const user = useAuth((s) => s.user);
  const p = useLocale((s) => s.dict.profile);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();

  if (!user || user.id === ownerId || isFollowing === null || isFollowing === undefined) {
    return null;
  }

  const toggleFollow = useMutation({
    mutationFn: () => (isFollowing ? unfollow(ownerId) : follow(ownerId)),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["public-feed"] });
      void qc.invalidateQueries({ queryKey: ["following-feed"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      void qc.invalidateQueries({ queryKey: ["researcher", ownerId] });

      if (!isFollowing) {
        const firstFollow =
          typeof window !== "undefined" &&
          (sessionStorage.getItem(FIRST_FEED_FOLLOW_WELCOME_KEY) === "1" ||
            localStorage.getItem("quantlab-feed-follow-coach-dismissed") !== "1");
        if (firstFollow) {
          burstConfetti(1800);
          sessionStorage.removeItem(FIRST_FEED_FOLLOW_WELCOME_KEY);
        }
        void trackEvent("feed_card_follow", { owner_id: ownerId, report_id: reportId });
      } else {
        void trackEvent("feed_card_unfollow", { owner_id: ownerId, report_id: reportId });
      }

      notify(isFollowing ? p.unfollowed : p.followed, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, p.followFail), "error"),
  });

  return (
    <button
      type="button"
      className={
        isFollowing
          ? compact
            ? "btn-ghost text-xs"
            : "btn-ghost text-sm"
          : compact
            ? "btn-primary text-xs"
            : "btn-primary text-sm"
      }
      disabled={toggleFollow.isPending}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleFollow.mutate();
      }}
    >
      {isFollowing ? p.followingBtn : p.follow}
    </button>
  );
}

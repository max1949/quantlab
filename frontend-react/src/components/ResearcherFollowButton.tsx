import { useMutation, useQueryClient } from "@tanstack/react-query";
import { follow, trackEvent, unfollow } from "../api/endpoints";
import type { ResearchJourney } from "../api/types";
import { apiErrorMessage } from "../api/client";
import { burstConfetti } from "../lib/confetti";
import {
  FIRST_FEED_FOLLOW_WELCOME_KEY,
  FIRST_FOLLOWING_FEED_WELCOME_KEY,
} from "../lib/onboardingFocus";
import { journeyFollowingCount, NETWORK_FOLLOW_TARGET } from "../lib/journeyFollowing";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

const DISMISS_KEY = "quantlab-feed-follow-coach-dismissed";

type Props = {
  ownerId: string;
  isFollowing?: boolean | null;
  reportId?: string;
  compact?: boolean;
  followEvent?: string;
  unfollowEvent?: string;
};

export default function ResearcherFollowButton({
  ownerId,
  isFollowing,
  reportId,
  compact = false,
  followEvent = "feed_card_follow",
  unfollowEvent = "feed_card_unfollow",
}: Props) {
  const user = useAuth((s) => s.user);
  const p = useLocale((s) => s.dict.profile);
  const fc = useLocale((s) => s.dict.feedFollowCoach);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();

  if (!user || user.id === ownerId || isFollowing === null || isFollowing === undefined) {
    return null;
  }

  const toggleFollow = useMutation({
    mutationFn: () => (isFollowing ? unfollow(ownerId) : follow(ownerId)),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["public-feed"] }),
        qc.invalidateQueries({ queryKey: ["following-feed"] }),
        qc.refetchQueries({ queryKey: ["research-journey"] }),
        qc.invalidateQueries({ queryKey: ["researcher", ownerId] }),
      ]);

      if (!isFollowing) {
        if (sessionStorage.getItem(FIRST_FEED_FOLLOW_WELCOME_KEY) === "1") {
          burstConfetti(1800);
          sessionStorage.removeItem(FIRST_FEED_FOLLOW_WELCOME_KEY);
        }
        void trackEvent(followEvent, { owner_id: ownerId, report_id: reportId });

        const journey = qc.getQueryData<ResearchJourney>(["research-journey"]);
        const followingCount = journeyFollowingCount(journey);
        if (followingCount >= NETWORK_FOLLOW_TARGET) {
          burstConfetti(3600);
          localStorage.setItem(DISMISS_KEY, "1");
          sessionStorage.setItem(FIRST_FOLLOWING_FEED_WELCOME_KEY, "1");
          notify(fc.networkReady, "success");
        } else if (followingCount > 0) {
          notify(fc.progressToast(followingCount, NETWORK_FOLLOW_TARGET), "success");
        } else {
          notify(p.followed, "success");
        }
      } else {
        notify(p.unfollowed, "success");
        void trackEvent(unfollowEvent, { owner_id: ownerId, report_id: reportId });
      }
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

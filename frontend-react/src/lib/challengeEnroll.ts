import type { ChallengeProgress } from "../api/types";
import { academyRewardMessage } from "./academy";
import { burstConfetti } from "./confetti";

type Notify = (message: string, kind?: "success" | "error" | "info") => void;

export type ChallengeEnrollLabels = {
  enrollSuccess: string;
  enrollSynced: (lit: number, total: number) => string;
  enrollReward: (pts: number, lit: number, total: number) => string;
  academyXpEarned: (title: string, xp: number) => string;
};

export function celebrateChallengeEnroll(
  data: ChallengeProgress,
  labels: ChallengeEnrollLabels,
  notify: Notify,
  options?: { confetti?: boolean },
): void {
  if (options?.confetti !== false) burstConfetti();

  const lit = data.milestones.filter((m) => m.completed).length;
  if (data.newly_awarded_points > 0) {
    notify(labels.enrollReward(data.newly_awarded_points, lit, data.total), "success");
  } else if (lit > 0) {
    notify(labels.enrollSynced(lit, data.total), "success");
  } else {
    notify(labels.enrollSuccess, "success");
  }

  const xpMsg = academyRewardMessage(data.academy_rewards, labels.academyXpEarned);
  if (xpMsg) notify(xpMsg, "success");
}

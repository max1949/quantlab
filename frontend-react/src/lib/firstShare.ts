import type { AcademyReward, ShareOut } from "../api/types";
import type { AcademyTaskLabel } from "./academy";
import { academyRewardMessage } from "./academy";
import { burstConfetti } from "./confetti";

type Notify = (message: string, kind?: "success" | "error" | "info") => void;

export type FirstShareLabels = {
  celebrate: string;
  academyXpEarned: (title: string, xp: number) => string;
  academyTaskLabels?: Record<string, AcademyTaskLabel>;
};

function isFirstShare(rewards?: AcademyReward[]): boolean {
  return Boolean(rewards?.some((r) => r.code === "first-share"));
}

/** Confetti + academy XP when the user creates their first share card. */
export function celebrateFirstShare(
  res: ShareOut,
  labels: FirstShareLabels,
  notify: Notify,
  options?: { confetti?: boolean },
): boolean {
  const first = isFirstShare(res.academy_rewards);
  if (!first) return false;

  if (options?.confetti !== false) burstConfetti();
  notify(labels.celebrate, "success");
  const xpMsg = academyRewardMessage(
    res.academy_rewards,
    labels.academyXpEarned,
    labels.academyTaskLabels,
  );
  if (xpMsg) notify(xpMsg, "success");
  return true;
}

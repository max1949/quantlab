import type { AcademyReward, ShareOut } from "../api/types";
import { academyRewardMessage } from "./academy";
import { burstConfetti } from "./confetti";

type Notify = (message: string, kind?: "success" | "error" | "info") => void;

export type FirstShareLabels = {
  celebrate: string;
  academyXpEarned: (title: string, xp: number) => string;
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
  const xpMsg = academyRewardMessage(res.academy_rewards, labels.academyXpEarned);
  if (xpMsg) notify(xpMsg, "success");
  return true;
}

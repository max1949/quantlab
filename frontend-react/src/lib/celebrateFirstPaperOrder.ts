import type { AcademyReward, PaperOrder } from "../api/types";
import type { AcademyTaskLabel } from "./academy";
import { academyRewardMessage } from "./academy";
import { burstConfetti } from "./confetti";

type Notify = (message: string, kind?: "success" | "error" | "info") => void;

export type FirstPaperOrderLabels = {
  celebrate: string;
  academyXpEarned: (title: string, xp: number) => string;
  academyTaskLabels?: Record<string, AcademyTaskLabel>;
};

function isFirstPaperOrder(rewards?: AcademyReward[]): boolean {
  return Boolean(rewards?.some((r) => r.code === "first-paper-order"));
}

/** Confetti when the user submits their first paper simulated order. */
export function celebrateFirstPaperOrder(
  res: PaperOrder,
  labels: FirstPaperOrderLabels,
  notify: Notify,
  options?: { confetti?: boolean },
): boolean {
  const first = isFirstPaperOrder(res.academy_rewards);
  if (!first) return false;

  if (options?.confetti !== false) burstConfetti(3000);
  notify(labels.celebrate, "success");
  const xpMsg = academyRewardMessage(
    res.academy_rewards,
    labels.academyXpEarned,
    labels.academyTaskLabels,
  );
  if (xpMsg) notify(xpMsg, "success");
  return true;
}

import type { AcademyReward, ReportDetail } from "../api/types";
import { academyRewardMessage } from "./academy";
import { burstConfetti } from "./confetti";

type Notify = (message: string, kind?: "success" | "error" | "info") => void;

export type FirstReportLabels = {
  celebrate: string;
  academyXpEarned: (title: string, xp: number) => string;
};

function isFirstReport(rewards?: AcademyReward[]): boolean {
  return Boolean(rewards?.some((r) => r.code === "first-report"));
}

/** Confetti when the user generates their first mastery report. */
export function celebrateFirstReport(
  res: ReportDetail,
  labels: FirstReportLabels,
  notify: Notify,
  options?: { confetti?: boolean },
): boolean {
  const first = isFirstReport(res.academy_rewards);
  if (!first) return false;

  if (options?.confetti !== false) burstConfetti(2800);
  notify(labels.celebrate, "success");
  const xpMsg = academyRewardMessage(res.academy_rewards, labels.academyXpEarned);
  if (xpMsg) notify(xpMsg, "success");
  return true;
}

import type { AcademyReward } from "../api/types";

export function academyRewardMessage(
  rewards: AcademyReward[] | undefined,
  format: (title: string, xp: number) => string,
): string | null {
  if (!rewards?.length) return null;
  const total = rewards.reduce((s, r) => s + r.awarded_xp, 0);
  if (rewards.length === 1) {
    return format(rewards[0].title, rewards[0].awarded_xp);
  }
  return format(rewards.map((r) => r.title).join(" · "), total);
}

/** 完成研究动作后自动点亮的学院任务 (无需手动领取)。 */
export const AUTO_ACADEMY_TASK_CODES = new Set([
  "welcome",
  "first-observation",
  "first-backtest",
  "first-validation",
  "first-report",
  "use-template-factor",
  "combine-factors",
  "write-formula-factor",
  "write-python-factor",
]);

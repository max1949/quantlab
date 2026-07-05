import type { AcademyReward } from "../api/types";

export type AcademyTaskLabel = { title: string; description: string };

export function localizedAcademyTitle(
  code: string,
  fallback: string,
  labels?: Record<string, AcademyTaskLabel>,
): string {
  return labels?.[code]?.title ?? fallback;
}

export function academyRewardMessage(
  rewards: AcademyReward[] | undefined,
  format: (title: string, xp: number) => string,
  taskLabels?: Record<string, AcademyTaskLabel>,
): string | null {
  if (!rewards?.length) return null;
  const total = rewards.reduce((s, r) => s + r.awarded_xp, 0);
  if (rewards.length === 1) {
    const r = rewards[0];
    return format(localizedAcademyTitle(r.code, r.title, taskLabels), r.awarded_xp);
  }
  return format(
    rewards.map((r) => localizedAcademyTitle(r.code, r.title, taskLabels)).join(" · "),
    total,
  );
}

/** 完成研究动作后自动点亮的学院任务 (无需手动领取)。 */
export const AUTO_ACADEMY_TASK_CODES = new Set([
  "welcome",
  "first-observation",
  "first-backtest",
  "first-validation",
  "first-report",
  "first-publish",
  "first-share",
  "challenge-enroll",
  "use-template-factor",
  "first-factor-scan",
  "combine-factors",
  "write-formula-factor",
  "write-python-factor",
  "first-paper-order",
  "paper-decay-review",
  "network-radar",
  "master-replication",
]);

import type { ResearchJourney } from "../api/types";

/** 新手人脉孵化目标：关注 2～3 位大师。 */
export const NETWORK_FOLLOW_TARGET = 3;

export function journeyFollowingCount(journey: ResearchJourney | undefined): number {
  if (!journey) return 0;
  return (
    journey.share_growth_coaching?.following ??
    journey.mastery_graduation_coaching?.following ??
    0
  );
}

import type { ResearchJourney } from "../api/types";
import { FIRST_MENTOR_WELCOME_KEY, FIRST_PAPER_ORDER_WELCOME_KEY } from "./onboardingFocus";

export type IncubationCoachId =
  | "checkout"
  | "graduation"
  | "first_paper_order"
  | "first_report"
  | "org_member"
  | "reputation"
  | "share_growth"
  | "first_mentor"
  | "quickstart"
  | "revisit"
  | "mastery_overview";

export const INCUBATION_COACH_PRIORITY: IncubationCoachId[] = [
  "checkout",
  "graduation",
  "first_paper_order",
  "first_report",
  "org_member",
  "reputation",
  "share_growth",
  "first_mentor",
  "quickstart",
  "revisit",
  "mastery_overview",
];

function ls(key: string): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(key);
}

function isQuickstartDismissed(journey: ResearchJourney): boolean {
  const guide = journey.quickstart_guide;
  if (!guide) return true;
  const raw = ls("quantlab-quickstart-dismissed");
  if (!raw || raw === "1") return raw === "1";
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n >= guide.progress;
}

export function listActiveIncubationCoaches(
  journey: ResearchJourney | undefined,
  opts: { checkoutActive: boolean; firstMentorVisible: boolean },
): IncubationCoachId[] {
  if (!journey) return [];

  const active: IncubationCoachId[] = [];

  if (opts.checkoutActive && journey.checkout_coaching) {
    active.push("checkout");
  }
  if (journey.mastery_graduation_coaching && ls("quantlab-mastery-graduation-dismissed") !== "1") {
    active.push("graduation");
  }
  const paperCoach = journey.first_paper_order_coaching;
  if (
    paperCoach?.active_project_id &&
    ls(`quantlab-first-paper-order-coach-${paperCoach.active_project_id}`) !== "1"
  ) {
    active.push("first_paper_order");
  }
  if (journey.first_report_coaching && ls("quantlab-first-report-dismissed") !== "1") {
    active.push("first_report");
  }
  const orgCoach = journey.org_member_coaching;
  if (orgCoach && ls(`quantlab-org-member-coach-${orgCoach.org_id}`) !== "1") {
    active.push("org_member");
  }
  if (journey.reputation_coaching && ls("quantlab-reputation-coach-dismissed") !== "1") {
    const defer =
      typeof window !== "undefined" &&
      (sessionStorage.getItem(FIRST_PAPER_ORDER_WELCOME_KEY) ||
        sessionStorage.getItem("quantlab-first-leaderboard-paper-welcome") ||
        sessionStorage.getItem("quantlab-first-paper-graduation-welcome"));
    if (!defer) active.push("reputation");
  }
  if (
    journey.share_growth_coaching &&
    !journey.mastery_graduation_coaching &&
    ls("quantlab-share-growth-coach-dismissed") !== "1"
  ) {
    active.push("share_growth");
  }
  if (opts.firstMentorVisible) {
    active.push("first_mentor");
  } else if (
    ls("quantlab-first-mentor-welcome-dismissed") !== "1" &&
    typeof window !== "undefined" &&
    sessionStorage.getItem(FIRST_MENTOR_WELCOME_KEY) === "1"
  ) {
    active.push("first_mentor");
  }
  if (journey.quickstart_guide && !isQuickstartDismissed(journey)) {
    active.push("quickstart");
  }
  if (journey.research_revisit_coaching && ls("quantlab-research-revisit-coach-dismissed") !== "1") {
    active.push("revisit");
  }
  if (journey.mastery_overview && ls("quantlab-mastery-overview-dismissed") !== "1") {
    active.push("mastery_overview");
  }

  const ordered = INCUBATION_COACH_PRIORITY.filter((id) => active.includes(id));
  const mentorPinned =
    typeof window !== "undefined" &&
    (sessionStorage.getItem(FIRST_MENTOR_WELCOME_KEY) === "1" || opts.firstMentorVisible) &&
    ordered.includes("first_mentor");
  if (mentorPinned) {
    return ["first_mentor", ...ordered.filter((id) => id !== "first_mentor")];
  }
  return ordered;
}

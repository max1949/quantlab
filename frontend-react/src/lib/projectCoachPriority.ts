import type { ResearchJourney } from "../api/types";
import {
  FIRST_BACKTEST_WELCOME_KEY,
  FIRST_PAPER_ORDER_WELCOME_KEY,
  FIRST_PROJECT_WELCOME_KEY,
  FIRST_VALIDATION_WELCOME_KEY,
} from "./onboardingFocus";

export type ProjectCoachId =
  | "first_paper_order"
  | "first_validation"
  | "first_backtest"
  | "first_project";

export const PROJECT_COACH_PRIORITY: ProjectCoachId[] = [
  "first_paper_order",
  "first_validation",
  "first_backtest",
  "first_project",
];

function ls(key: string): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(key);
}

export type ProjectCoachProgress = {
  projectId: string;
  backtestDone: boolean;
  validationDone: boolean;
  reportDone: boolean;
};

export function listActiveProjectCoaches(
  journey: ResearchJourney | undefined,
  progress: ProjectCoachProgress,
): ProjectCoachId[] {
  if (!journey) return [];
  const { projectId, backtestDone, validationDone } = progress;
  const active: ProjectCoachId[] = [];

  const paper = journey.first_paper_order_coaching;
  if (
    paper?.active_project_id === projectId &&
    ls(`quantlab-first-paper-order-coach-${projectId}`) !== "1"
  ) {
    active.push("first_paper_order");
  }

  const validation = journey.first_validation_coaching;
  if (
    validation?.active_project_id === projectId &&
    validationDone &&
    !progress.reportDone &&
    ls(`quantlab-first-validation-coach-${projectId}`) !== "1"
  ) {
    active.push("first_validation");
  }

  const backtest = journey.first_backtest_coaching;
  if (
    backtest?.active_project_id === projectId &&
    backtestDone &&
    !validationDone &&
    ls(`quantlab-first-backtest-coach-${projectId}`) !== "1"
  ) {
    active.push("first_backtest");
  }

  const project = journey.first_project_coaching;
  if (
    project?.active_project_id === projectId &&
    !backtestDone &&
    ls(`quantlab-first-project-coach-${projectId}`) !== "1"
  ) {
    active.push("first_project");
  }

  const ordered = PROJECT_COACH_PRIORITY.filter((id) => active.includes(id));
  if (typeof window === "undefined") return ordered;

  const pin: ProjectCoachId | null =
    sessionStorage.getItem(FIRST_PAPER_ORDER_WELCOME_KEY) === projectId
      ? "first_paper_order"
      : sessionStorage.getItem(FIRST_VALIDATION_WELCOME_KEY) === projectId
        ? "first_validation"
        : sessionStorage.getItem(FIRST_BACKTEST_WELCOME_KEY) === projectId
          ? "first_backtest"
          : sessionStorage.getItem(FIRST_PROJECT_WELCOME_KEY) === projectId
            ? "first_project"
            : null;

  if (pin && ordered.includes(pin)) {
    return [pin, ...ordered.filter((id) => id !== pin)];
  }
  return ordered;
}

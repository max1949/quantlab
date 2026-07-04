import type { Dictionary } from "../i18n/dictionaries";

// Map backend next-step stage to SPA routes.
export function stageToRoute(
  stage: string,
  recommendedTemplate?: string | null,
  activeProjectId?: string | null,
): string {
  switch (stage) {
    case "create_project":
      return recommendedTemplate
        ? `/templates?focus=${encodeURIComponent(recommendedTemplate)}`
        : "/templates";
    case "create_factor":
    case "run_backtest":
    case "run_validation":
    case "run_paper":
    case "generate_report":
    case "publish_share":
      return activeProjectId ? `/projects/${activeProjectId}` : "/projects";
    case "keep_going":
    default:
      return "/feed";
  }
}

export function stageToCtaLabel(stage: string, stages: Dictionary["stages"]): string {
  const key = stage as keyof Dictionary["stages"];
  return stages[key] ?? stages.keep_going;
}

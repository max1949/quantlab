import type { Dictionary } from "../i18n/dictionaries";

// Map backend next-step stage to SPA routes.
export function stageToRoute(
  stage: string,
  recommendedTemplate?: string | null,
  activeProjectId?: string | null,
  regimeSymbol?: string | null,
): string {
  switch (stage) {
    case "create_project": {
      const q = new URLSearchParams();
      if (recommendedTemplate) q.set("focus", recommendedTemplate);
      if (regimeSymbol && regimeSymbol !== "RB") q.set("symbol", regimeSymbol);
      const qs = q.toString();
      return qs ? `/templates?${qs}` : "/templates";
    }
    case "create_factor":
    case "run_backtest":
    case "run_validation":
    case "run_paper":
    case "revalidate_decay":
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

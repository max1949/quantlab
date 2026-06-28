// 把后端 next-step 的 stage 映射成前端路由。
// 后端 cta_path 是后端语义路径, 这里按 stage 统一翻译成 SPA 路由。
export function stageToRoute(
  stage: string,
  recommendedTemplate?: string | null,
): string {
  switch (stage) {
    case "create_project":
      return recommendedTemplate
        ? `/templates?focus=${encodeURIComponent(recommendedTemplate)}`
        : "/templates";
    case "create_factor":
    case "run_backtest":
    case "run_validation":
    case "generate_report":
    case "publish_share":
      return "/projects";
    case "keep_going":
    default:
      return "/feed";
  }
}

export function stageToCtaLabel(stage: string): string {
  switch (stage) {
    case "create_project":
      return "从模板开始 →";
    case "create_factor":
      return "去造因子 →";
    case "run_backtest":
      return "去跑回测 →";
    case "run_validation":
      return "去做验证 →";
    case "generate_report":
      return "去生成报告 →";
    case "publish_share":
      return "去发布分享 →";
    default:
      return "继续研究 →";
  }
}

/** 标的 → 默认推荐研究模板 (与后端 template_service 种子一致)。 */
import { FOLLOWING_TEMPLATE_HANDOFF_KEY } from "./onboardingFocus";

export const PRIMARY_TEMPLATE_BY_SYMBOL: Record<string, string> = {
  AU: "gold-trend",
  RB: "commodity-momentum",
  IF: "vol-regime",
};

export const REGIME_TEMPLATE_SYMBOLS = new Set(["RB", "AU", "IF"]);

export function primaryTemplateForSymbol(symbol: string): string | null {
  const key = symbol.trim().toUpperCase();
  return PRIMARY_TEMPLATE_BY_SYMBOL[key] ?? null;
}

/** Deep-link to templates with focus + symbol for master-replication handoff. */
export function buildTemplatesHandoffPath(symbol: string, templateCode?: string | null): string {
  const code = templateCode ?? primaryTemplateForSymbol(symbol);
  const sym = symbol.trim().toUpperCase();
  const params = new URLSearchParams();
  if (code) params.set("focus", code);
  if (REGIME_TEMPLATE_SYMBOLS.has(sym)) params.set("symbol", sym);
  const qs = params.toString();
  return qs ? `/templates?${qs}` : "/templates";
}

export function armFollowingTemplateHandoff(symbol: string): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(FOLLOWING_TEMPLATE_HANDOFF_KEY, symbol);
}

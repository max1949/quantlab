/** 标的 → 默认推荐研究模板 (与后端 template_service 种子一致)。 */
export const PRIMARY_TEMPLATE_BY_SYMBOL: Record<string, string> = {
  AU: "gold-trend",
  RB: "commodity-momentum",
  IF: "vol-regime",
};

export function primaryTemplateForSymbol(symbol: string): string | null {
  const key = symbol.trim().toUpperCase();
  return PRIMARY_TEMPLATE_BY_SYMBOL[key] ?? null;
}

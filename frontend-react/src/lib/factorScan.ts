/** 扫描实验类型展示 (组合扫描现存 "stack"；兼容历史 stack:uuid,uuid) */
export function formatScanType(templateType: string): string {
  if (templateType === "stack" || templateType.startsWith("stack:")) return "stack";
  return templateType;
}

export function isStackScanType(templateType: string): boolean {
  return templateType === "stack" || templateType.startsWith("stack:");
}

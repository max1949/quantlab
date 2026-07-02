/** 扫描实验类型展示 (组合扫描存 stack:uuid,uuid) */
export function formatScanType(templateType: string): string {
  if (templateType.startsWith("stack:")) return "stack";
  return templateType;
}

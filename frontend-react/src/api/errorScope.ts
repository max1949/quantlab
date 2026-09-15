/**
 * Error presentation scope helpers.
 * SUCCESS_RESULT_AND_FATAL_ERROR_COEXIST=DENY
 * AUXILIARY_ERROR_SCOPED=YES
 * REAL_ORDER_WARNING_ON_FACTOR_SCAN=REMOVE
 */

export type ApiErrorDomain = "generic" | "trading" | "scan" | "auxiliary";

export function serverErrorCopy(domain: ApiErrorDomain = "generic"): string {
  if (domain === "trading") {
    return "服务暂时异常。请稍后重试；若持续出现，请联系运维。不会创建真实订单。";
  }
  if (domain === "scan") {
    return "扫描暂时未完成，请稍后重试。";
  }
  if (domain === "auxiliary") {
    return "扫描结果已生成，部分辅助信息暂时不可用。";
  }
  return "服务暂时异常。请稍后重试；若持续出现，请联系运维。";
}

/** Fatal global toast must not claim whole-operation failure when main task succeeded. */
export function allowGlobalFatalToast(opts: {
  mainTaskSucceeded: boolean;
  errorIsAuxiliary: boolean;
}): boolean {
  if (opts.mainTaskSucceeded && opts.errorIsAuxiliary) return false;
  if (opts.mainTaskSucceeded) return false;
  return true;
}

export function factorScanPageForbidsRealOrderCopy(message: string): boolean {
  return !/不会创建真实订单/.test(message);
}

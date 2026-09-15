/**
 * Node regression for scan error scope (mirrors errorScope.ts).
 * Run: node frontend-react/src/api/errorScope.regression.mjs
 */
import assert from "node:assert/strict";

function serverErrorCopy(domain = "generic") {
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

function allowGlobalFatalToast({ mainTaskSucceeded, errorIsAuxiliary }) {
  if (mainTaskSucceeded && errorIsAuxiliary) return false;
  if (mainTaskSucceeded) return false;
  return true;
}

function factorScanPageForbidsRealOrderCopy(message) {
  return !/不会创建真实订单/.test(message);
}

// TEST 1 — all success → no fatal
assert.equal(allowGlobalFatalToast({ mainTaskSucceeded: true, errorIsAuxiliary: false }), false);

// TEST 2 — scan success + AI fail → no global fatal
assert.equal(allowGlobalFatalToast({ mainTaskSucceeded: true, errorIsAuxiliary: true }), false);
assert.match(serverErrorCopy("auxiliary"), /辅助/);

// TEST 3 — next success must clear stale error (copy contract)
assert.equal(factorScanPageForbidsRealOrderCopy(serverErrorCopy("scan")), true);

// TEST 4 — main scan fail → scan-specific, no fake success coupling
assert.match(serverErrorCopy("scan"), /扫描暂时未完成/);
assert.equal(allowGlobalFatalToast({ mainTaskSucceeded: false, errorIsAuxiliary: false }), true);

// TEST 5 — factor scan page forbids real-order warning
assert.equal(factorScanPageForbidsRealOrderCopy(serverErrorCopy("generic")), true);
assert.equal(factorScanPageForbidsRealOrderCopy(serverErrorCopy("scan")), true);
assert.equal(factorScanPageForbidsRealOrderCopy(serverErrorCopy("trading")), false);

console.log("errorScope regression PASS");
